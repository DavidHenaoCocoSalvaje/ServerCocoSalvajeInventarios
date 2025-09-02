# app/routers/inventario.py
from enum import Enum
import traceback
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request, status


from app.internal.gen.utilities import DateTz
from app.internal.integrations.shopify import ShopifyGraphQLClient, get_inventory_info, persistir_inventory_info
from app.models.pydantic.world_office.general import WOCiudad
from app.models.pydantic.world_office.terceros import WODireccion, WOTerceroCreate
from app.internal.integrations.world_office import WoClient
from app.models.db.transacciones import PedidoCreate
from app.models.db.session import get_async_session
from app.models.pydantic.shopify.order import Order, OrderResponse, OrderWebHook
from app.models.pydantic.world_office.facturacion import WODocumentoVentaCreate, WOReglone
from app.routers.base import CRUD
from app.internal.log import LogLevel, factory_logger

# Seguridad
from app.routers.auth import hmac_validation_shopify

# Facturacion
from app.config import config

from app.models.db.inventario import (
    Bodega,
    Elemento,
    VarianteElemento,
    ComponentesPorVariante,
    Grupo,
    TipoMovimiento,
    TipoPrecio,
    TiposMedida,
    MedidasPorVariante,
    PreciosPorVariante,
    Movimiento,
    EstadoVariante,
    Medida,
)

# Base de datos (Repositorio)
from app.internal.query.inventario import (
    bodega_query,
    grupo_query,
    elemento_query,
    variante_elemento_query,
    componentes_por_variante_query,
    unidad_medida_query,
    precio_variante_query,
    tipo_precio_query,
    tipo_medida_query,
    medidas_por_variante_query,
    movimiento_query,
    tipo_movimiento_query,
    estado_elemento_query,
)
from app.internal.query.transacciones import (
    pedido_query,
)
from app.routers.auth import validar_access_token

log_inventario = factory_logger('inventario', file=True)
log_inventario_shopify = factory_logger('inventario_shopify', file=True)
log_debug = factory_logger('debug', level=LogLevel.DEBUG, file=False)


class Tags(Enum):
    INVENTARIO = 'Inventario'
    SHOPIFY = 'Shopify'


router = APIRouter(
    prefix='/inventario',
    tags=[Tags.INVENTARIO],
    responses={404: {'description': 'No encontrado'}},
    dependencies=[Depends(validar_access_token)],
)

shopify_router = APIRouter(
    prefix='/inventario/shopify',
    tags=[Tags.INVENTARIO, Tags.SHOPIFY],
    responses={404: {'description': 'No encontrado'}},
)


# Llamadas a la función genérica para cada modelo de inventario
CRUD[Elemento](
    router,
    elemento_query,
    'elemento',
)
CRUD[VarianteElemento](
    router,
    variante_elemento_query,
    'variante',
)
CRUD[ComponentesPorVariante](
    router,
    componentes_por_variante_query,
    'componente',
)
CRUD[Bodega](
    router,
    bodega_query,
    'bodega',
)
CRUD[Grupo](
    router,
    grupo_query,
    'grupo',
)
CRUD[Medida](
    router,
    unidad_medida_query,
    'unidad_medida',
)
CRUD[PreciosPorVariante](
    router,
    precio_variante_query,
    'precio',
)
CRUD[TipoPrecio](
    router,
    tipo_precio_query,
    'tipo_precio',
)
CRUD[TiposMedida](
    router,
    tipo_medida_query,
    'tipo_medida',
)
CRUD[MedidasPorVariante](
    router,
    medidas_por_variante_query,
    'medida',
)
CRUD[Movimiento](
    router,
    movimiento_query,
    'movimiento',
)
CRUD[TipoMovimiento](
    router,
    tipo_movimiento_query,
    'tipo_movimiento',
)
CRUD[EstadoVariante](
    router,
    estado_elemento_query,
    'estado',
)


# Sincronización
@shopify_router.post(
    '/sync_shopify',
    response_model=bool,
    summary='Sincroniza inventarios de Shopify con base de datos',
    description='Se registran movimiento de cargue.',
    status_code=status.HTTP_200_OK,
    tags=[Tags.INVENTARIO, Tags.SHOPIFY],
    dependencies=[Depends(validar_access_token)],
)
async def sync_shopify():
    """Sincroniza los datos de inventario desde Shopify."""
    try:
        shopify_client = ShopifyGraphQLClient()
        inventory_info = await get_inventory_info(shopify_client)
        await persistir_inventory_info(inventory_info)
        log_inventario_shopify.debug('Inventarios de Shopify sincronizado con éxito')
        return True
    except Exception as e:
        log_inventario_shopify.error(f'Error al sincronizar inventarios de Shopify: {e}')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Pedidos
@shopify_router.post(
    '/pedido',
    status_code=status.HTTP_200_OK,
    tags=[Tags.INVENTARIO, Tags.SHOPIFY],
    dependencies=[Depends(hmac_validation_shopify)],
)
async def recibir_pedido_shopify(
    request: Request,
    background_tasks: BackgroundTasks,
):
    request_json = await request.json()
    shopify_client = ShopifyGraphQLClient()
    # Obtener datos de pedido
    order_webhook = OrderWebHook(**request_json)
    # Se consulta la orden porque la información que viene del webhook no incluye la información de la transacción.
    try:
        order_json = await shopify_client.get_order(order_webhook.admin_graphql_api_id)
    except Exception as e:
        # No se lanza excepción porque es un webhook, se registra únicamente en el log y se responde Ok para no recibir el mismo webhook.
        log_inventario_shopify.error(f'{e}, {traceback.format_exc()}')
        return True

    order_response = OrderResponse(**order_json)
    if not order_response.valid():
        log_inventario_shopify.error(f'Order void: {order_response.model_dump_json()}, shopify_response: {order_json}')
        return

    if order_response.data.order is None:
        log_inventario_shopify.error(f'Order not found: {order_response.model_dump_json()}')
    order = order_response.data.order

    """Se evidencia que shopify en ocasiones intenta enviar el mismo pedido varias veces.
    Se evita usando BackgroundTasks pos si es a causa de un TimeoutError."""
    background_tasks.add_task(procesar_pedido_shopify, order)

    return True


async def procesar_pedido_shopify(order: Order):  # BackgroundTasks No lanzar excepciones.
    async for session in get_async_session():
        pedido = await pedido_query.get_by_number(session, order.number)

        # Se registra pedido antes de crear factura por si algo sale mal tener un registro con el número de pedido y no duplicarlo.
        if pedido is None:
            pedido_create = PedidoCreate(numero=str(order.number))
            pedido = await pedido_query.create(session, pedido_create)

        if not pedido.id:
            return

        wo_client = WoClient()
        identificacion_tercero = order.billingAddress.identificacion or order.shippingAddress.identificacion
        if not pedido.factura_id:
            # Cuando un cliente realiza una compra en shopify, El documento de identidad se solicita en el campo "company" en la dirección de facturación.
            if not identificacion_tercero:
                msg = 'Falta documento de identidad'
                pedido_update = pedido.model_copy()
                pedido_update.log = msg
                await pedido_query.update(session, pedido, pedido_update, pedido.id)

                log_inventario_shopify.debug(msg)
                return

        if not order.fullyPaid:
            msg = f'No se registra pago: fyllyPaid: {order.fullyPaid}'
            pedido_update = pedido.model_copy()
            pedido_update.log = msg
            await pedido_query.update(session, pedido, pedido_update, pedido.id)
            return

        try:
            factura = await facturar_orden(wo_client, order, identificacion_tercero)
        except Exception as e:
            pedido_update = pedido.model_copy()
            pedido_update.log = str(e)
            await pedido_query.update(session, pedido, pedido_update, pedido.id)
            return

        # Se registra número de factura por si pasa algo antes de contabilizar.
        pedido_update = pedido.model_copy()
        pedido_update.factura_id = str(factura.id)
        pedido_update.factura_numero = str(factura.numero)

        pedido = await pedido_query.update(session, pedido, pedido_update, pedido.id)
        if not pedido.id:
            return

        try:
            factura = await wo_client.get_documento_venta(int(pedido.factura_id))
            contabilizar = await wo_client.contabilizar_documento_venta(int(pedido.factura_id))
            if not pedido.contabilizado:
                pedido_update = pedido.model_copy()
                pedido_update.contabilizado = contabilizar
                pedido = await pedido_query.update(session, pedido, pedido_update, pedido.id)

        except Exception as e:
            pedido_update = pedido.model_copy()
            pedido_update.log = str(e)
            await pedido_query.update(session, pedido, pedido_update, pedido.id)
            return

        log_debug.info(f'Pedido procesado: {order.number}, factura: {pedido.factura_numero}')


async def facturar_orden(wo_client: WoClient, order: Order, identificacion_tercero: str):
    # Cuando un cliente realiza una compra en shopify, El documento de identidad se solicita en el campo "company" en la dirección de facturación.
    ciudad = order.billingAddress.city or order.shippingAddress.city
    departamento = order.billingAddress.province or order.shippingAddress.province
    telefono = order.billingAddress.telefono or order.shippingAddress.telefono
    email = order.email if order.email else 'sinemail@mail.com'
    wo_ciudad = await wo_client.buscar_ciudad(departamento, ciudad)
    ciudad_id = wo_ciudad.id

    # El elemento 0 en la dirección es el documento de identidad, por lo cúal se omite.
    address = (
        ', '.join(order.billingAddress.formatted[1:])
        if order.billingAddress.formatted
        else ', '.join(order.shippingAddress.formatted[1:])
    )

    first_name = order.billingAddress.firstName or order.shippingAddress.firstName
    primer_nombre = first_name.split(' ')[0]
    segundo_nombre = first_name.split(' ')[1] if len(first_name.split(' ')) > 1 else ''

    last_name = order.billingAddress.lastName or order.shippingAddress.lastName
    primer_apellido = last_name.split(' ')[0]
    segundo_apellido = last_name.split(' ')[1] if len(last_name.split(' ')) > 1 else ''

    wo_tercero = await wo_client.get_tercero(identificacion_tercero)

    """ Cuando se crea un tercero, 
    la dirección tienen un nombre, este causa error si es un mombre muy largo,
    por lo cúal hace falta especificar el nombre para evitar errores. """
    direcciones = [
        WODireccion(
            nombre='Principal',
            direccion=address,
            senPrincipal=True,
            emailPrincipal=email,
            telefonoPrincipal=telefono,
            ubicacionCiudad=WOCiudad(
                id=ciudad_id,
            ),
        )
    ]

    if wo_tercero is None:
        tercero_create = WOTerceroCreate(
            idTerceroTipoIdentificacion=3,  # Cédula de ciudadanía
            identificacion=identificacion_tercero,
            primerNombre=primer_nombre,
            segundoNombre=segundo_nombre,
            primerApellido=primer_apellido,
            segundoApellido=segundo_apellido,
            idCiudad=ciudad_id,
            direccion=address,
            direcciones=direcciones,
            idTerceroTipos=[4],  # Cliente
            idTerceroTipoContribuyente=6,
            idClasificacionImpuestos=1,
            telefono=telefono,
            email=email,
            plazoDias=30,
            responsabilidadFiscal=[7],
        )
        wo_tercero = await wo_client.crear_tercero(tercero_create)

    if not wo_tercero.is_client() and wo_tercero.tieneDirPrincipal and wo_tercero.direccionPrincipal.direccion:
        id_tercero_tipos = wo_tercero.idTerceroTipos
        id_tercero_tipos.append(4)  # Cliente
        tercero_create = WOTerceroCreate(
            id=wo_tercero.id,
            idTerceroTipoIdentificacion=wo_tercero.terceroTipoIdentificacion.id,
            identificacion=identificacion_tercero,
            primerNombre=primer_nombre,
            segundoNombre=segundo_nombre,
            primerApellido=primer_apellido,
            segundoApellido=segundo_apellido,
            idCiudad=ciudad_id,
            direccion=address,
            direcciones=direcciones,
            idTerceroTipos=id_tercero_tipos,  # Cliente
            idTerceroTipoContribuyente=6,
            idClasificacionImpuestos=1,
            telefono=telefono,
            email=email,
            plazoDias=30,
            responsabilidadFiscal=[7],
        )
        wo_tercero = await wo_client.editar_tercero(tercero_create)

    reglones: list[WOReglone] = []
    for line_intem in order.lineItems.nodes:
        inventario = await wo_client.get_inventario_por_codigo(line_intem.sku)
        impuestos = inventario.impuestos
        generator = (
            impuesto_element.valor for impuesto_element in impuestos if impuesto_element.impuesto.tipo == 'IVA'
        )
        iva = next(generator, 0)
        # World Office adiciona el IVA automáticamente, se envía el precio con IVA descontado.
        valor_unitario = line_intem.discounted_unit_price_iva_discount(iva)

        kwargs = {}
        if line_intem.porc_discount > 0:
            kwargs['porDescuento'] = line_intem.porc_discount
        reglones.append(
            WOReglone(
                idInventario=inventario.id,
                unidadMedida='und',
                cantidad=line_intem.quantity,
                valorUnitario=valor_unitario,
                idBodega=1,
                **kwargs,
            )
        )

    costo_envio = int(order.shippingLine.originalPriceSet.shopMoney.amount)
    if costo_envio > 0:
        # El id de inventario que correspnde a FLETE en World Office es 1079
        reglones.append(
            WOReglone(idInventario=1079, unidadMedida='und', cantidad=1, valorUnitario=costo_envio, idBodega=1)
        )

    # Si los pagos son por wompi (contado), si son por addi (pse: contado, credito: credito, por defecto se deja en crédito)
    # 4 para contado, 5 para credito
    id_forma_pago = 4
    # if all(x.gateway == 'Addi Payment' for x in order.transactions):
    wo_documento_venta_create = WODocumentoVentaCreate(
        fecha=DateTz.today(),
        prefijo=config.wo_prefijo,  # 1 Sin prefijo, 13 FEFE
        documentoTipo='FV',
        concepto=config.wo_concepto,
        idEmpresa=1,  # CocoSalvaje
        idTerceroExterno=wo_tercero.id,
        idTerceroInterno=1,  # 1 CocoSalvaje, 1834 Lucy
        idFormaPago=id_forma_pago,
        idMoneda=31,
        reglones=reglones,
    )

    return await wo_client.crear_factura_venta(wo_documento_venta_create)
