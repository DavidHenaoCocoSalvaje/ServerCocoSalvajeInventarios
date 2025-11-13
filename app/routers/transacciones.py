from enum import Enum

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, UploadFile, status

from app.internal.integrations.shopify import ShopifyGraphQLClient
from app.internal.integrations.shopify_world_office import facturar_orden_shopify_world_office
from app.internal.log import factory_logger
from app.models.db.session import AsyncSessionDep
from app.models.db.transacciones import Pedido, PedidoCreate, PedidoLogs
from app.routers.auth import validar_access_token
from app.routers.base import CRUD
from app.internal.query.transacciones import PedidoQuery
from app.config import Environments, config
from pandas import read_csv, DataFrame, to_datetime
from io import BytesIO
from numpy import nan


class Tags(Enum):
    TRANSACCIONES = 'Transacciones'


router = APIRouter(
    prefix='/transacciones',
    tags=[Tags.TRANSACCIONES],
    responses={404: {'description': 'No encontrado'}},
    dependencies=[Depends(validar_access_token)],
)

CRUD(router, 'pedido', PedidoQuery(), Pedido, PedidoCreate)

log_transacciones = factory_logger('transacciones')


@router.post(
    '/facturar-pendientes',
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(validar_access_token)],
)
async def facturar_pendientes(
    session: AsyncSessionDep,
    background_tasks: BackgroundTasks,
):
    pedido_query = PedidoQuery()
    pedidos = await pedido_query.get_pendientes_facturar(session)
    log_transacciones.info(
        f'Se encontraron {len(pedidos)} pedidos pendientes de facturar, {[x.numero for x in pedidos]}'
    )

    if config.environment in [Environments.DEVELOPMENT.value, Environments.STAGING.value]:
        return True

    async def task(pedidos: list[Pedido]):
        for pedido in pedidos:
            if not pedido.numero:
                continue
            if pedido.log == PedidoLogs.NO_FACTURAR.value:
                continue
            orden = await ShopifyGraphQLClient().get_order_by_number(pedido.numero)
            if orden is None:
                log_transacciones.error(f'No se encontró orden con número {pedido.numero}')
            pedido_update = pedido.model_copy()
            pedido_update.q_intentos = pedido.q_intentos - 1
            await pedido_query.update(session, pedido_update, pedido.id)
            await facturar_orden_shopify_world_office(orden)

        log_transacciones.info(f'Se intentarón facturar los pedidios: {", ".join([str(x.numero) for x in pedidos])}')

    background_tasks.add_task(task, pedidos)
    return True


@router.post(
    '/facturar/{pedido_number}',
    dependencies=[Depends(validar_access_token)],
)
async def facturar_pedido(background_tasks: BackgroundTasks, pedido_number: int):
    if config.environment in [Environments.DEVELOPMENT.value, Environments.STAGING.value]:
        return True

    async def task(pedido_number: int):
        orden = await ShopifyGraphQLClient().get_order_by_number(pedido_number)
        if orden is None:
            log_transacciones.error(f'No se encontró orden con número {pedido_number}')
        await facturar_orden_shopify_world_office(orden)

    background_tasks.add_task(task, pedido_number)
    return True


@router.post(
    '/csv-addi',
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(validar_access_token)],
)
async def buscar_pedidos_csv_addi(files: list[UploadFile], session: AsyncSessionDep):
    if not len(files) == 1:
        return HTTPException(status_code=400, detail='Debe enviar un solo archivo')

    filename = files[0].filename
    if not filename:
        return HTTPException(status_code=400, detail='')

    if files[0].filename and not files[0].filename.endswith('.csv'):
        return HTTPException(status_code=400, detail='Debe enviar un archivo CSV')

    file = await files[0].read()
    buffer = BytesIO(file)
    df = read_csv(buffer, encoding='utf-8')
    # Normaliza \xa0, \t, \n, múltiples espacios, etc. a un solo espacio
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].str.split().str.join(' ')

    # Algunos pagos de aparecen en Addi como exitosos pero luego salen como Abandonados, se deben identificar y filtrar
    # Encontrar valors duplicados en campo "ID Orden" y Eliminar si el último tiene estado de "Abandono"\

    def parse_fecha(fecha_str):
        meses = {
            'ene': 'Jan',
            'feb': 'Feb',
            'mar': 'Mar',
            'abr': 'Apr',
            'jun': 'Jun',
            'jul': 'Jul',
            'ago': 'Aug',
            'sept': 'Sep',
            'oct': 'Oct',
            'nov': 'Nov',
            'dic': 'Dec',
        }
        # Reemplazar AM/PM
        fecha_str = fecha_str.replace('a. m.', 'AM').replace('p. m.', 'PM').replace('GMT-5', '-0500')
        # Reemplazar solo los meses necesarios
        for esp, eng in meses.items():
            fecha_str = fecha_str.replace(f' {esp} ', f' {eng} ')
        return to_datetime(fecha_str, format='%d %b %Y, %I:%M %p %z')

    df['Fecha Creación'] = df['Fecha Creación'].apply(parse_fecha).dt.tz_convert(config.local_timezone)
    df = df.sort_values(['Fecha Creación', 'ID Orden']).drop_duplicates(['Fecha Creación', 'ID Orden'], keep='last')

    # Filtrar solo por pagos exitosos y canal E_COMMERCE_SHOPIFY para encontrar los pedidos al consultar en Sopify, de lo contrario serán pedido que no se encontrarán
    # Solo mantenter órdenes a crédito que son las de interes para realizar menos peticiones a Shopify y tardar menos en responder
    df = df[(df['Estado'] == 'Exitosa') & (df['Canal'] == 'E_COMMERCE_SHOPIFY') & (df['Tipo de venta'] == 'Crédito')]

    if not len(df):
        return HTTPException(
            status_code=400,
            detail='No se encontraron pedidos exitosos, el archivo debe contener registros con estado Exitoso',
        )

    orders = await ShopifyGraphQLClient().get_orders_by_payment_ids(
        [payment_id for payment_id in df['ID Orden'].to_list()]
    )
    # Mapear ordenes por payment_id
    map_orders = {
        transaction.paymentId: order.number
        for order in orders
        for transaction in order.transactions
        if transaction.gateway == 'Addi Payment' and order.fullyPaid
    }

    df['orden'] = df['ID Orden'].map(lambda x: map_orders.get(x))

    pedidos = await PedidoQuery().get_by_numbers(session, [int(x) for x in df['orden'][df['orden'].notna()]])
    pedidos_df = DataFrame([pedido.model_dump() for pedido in pedidos])

    df = df.merge(pedidos_df, left_on='orden', right_on='numero', how='left')
    df = df.rename(columns={'CC': 'cc', 'Nombre Cliente': 'nombre_cliente', 'Tipo de venta': 'tipo_venta'})

    return (
        df[['fecha', 'numero', 'factura_id', 'contabilizado', 'cc', 'nombre_cliente', 'tipo_venta']]
        .replace(nan, None)
        .to_dict(orient='records')
    )
