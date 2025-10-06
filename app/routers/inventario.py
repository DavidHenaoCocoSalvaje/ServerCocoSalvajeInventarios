# app/routers/inventario.py
from datetime import date
from enum import Enum
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request, status
from pandas import DataFrame, Grouper
from pydantic import BaseModel

if __name__ == '__main__':
    from os.path import abspath
    from sys import path as sys_path

    sys_path.append(abspath('.'))


from app.internal.integrations.shopify import ShopifyInventario
from app.models.db.session import AsyncSessionDep
from app.internal.query.base import DateRange, Sort
from app.internal.query.inventario import (
    BodegaQuery,
    ComponentesPorVarianteQuery,
    ElementoQuery,
    EstadoVarianteQuery,
    GrupoQuery,
    MedidaQuery,
    MedidasPorVarianteQuery,
    MetaAtributoQuery,
    MetaValorQuery,
    MetadatosPorSoporteQuery,
    MovimientoQuery,
    PrecioPorVarianteQuery,
    TipoMovimientoQuery,
    TipoPrecioQuery,
    TipoSoporteQuery,
    TiposMedidaQuery,
    VarianteElementoQuery,
)
from app.models.pydantic.shopify.order import OrderWebHook
from app.routers.base import CRUD
from app.internal.log import LogLevel, factory_logger

# Seguridad
from app.routers.auth import hmac_validation_shopify

# Facturacion

from app.models.db.inventario import (
    Bodega,
    BodegaCreate,
    ComponentesPorVariante,
    ComponentesPorVarianteCreate,
    Elemento,
    ElementoCreate,
    EstadoVariante,
    EstadoVarianteCreate,
    Grupo,
    GrupoCreate,
    Medida,
    MedidaCreate,
    MedidasPorVariante,
    MedidasPorVarianteCreate,
    MetaAtributo,
    MetaValor,
    MetaValorCreate,
    Movimiento,
    MovimientoCreate,
    MovimientoRead,
    PreciosPorVariante,
    PreciosPorVarianteCreate,
    TipoMovimiento,
    TipoMovimientoCreate,
    TipoPrecio,
    TipoPrecioCreate,
    TiposMedida,
    TiposMedidaCreate,
    VarianteElemento,
    VarianteElementoCreate,
)

# Base de datos (Repositorio)
from app.routers.auth import validar_access_token
from app.routers.ul.facturacion import procesar_pedido_shopify

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

shopify_inventario_router = APIRouter(
    prefix='/inventario/shopify',
    tags=[Tags.INVENTARIO, Tags.SHOPIFY],
    responses={404: {'description': 'No encontrado'}},
)


# Llamadas a la función genérica para cada modelo de inventario
CRUD(router, 'elemento', ElementoQuery(), Elemento, ElementoCreate)
CRUD(router, 'variante', VarianteElementoQuery(), VarianteElemento, VarianteElementoCreate)
CRUD(router, 'componente', ComponentesPorVarianteQuery(), ComponentesPorVariante, ComponentesPorVarianteCreate)
CRUD(router, 'bodega', BodegaQuery(), Bodega, BodegaCreate)
CRUD(router, 'grupo', GrupoQuery(), Grupo, GrupoCreate)
CRUD(router, 'unidad-medida', MedidaQuery(), Medida, MedidaCreate)
CRUD(router, 'precio', PrecioPorVarianteQuery(), PreciosPorVariante, PreciosPorVarianteCreate)
CRUD(router, 'tipo-precio', TipoPrecioQuery(), TipoPrecio, TipoPrecioCreate)
CRUD(router, 'tipo-medida', TiposMedidaQuery(), TiposMedida, TiposMedidaCreate)
CRUD(router, 'medida', MedidasPorVarianteQuery(), MedidasPorVariante, MedidasPorVarianteCreate)
CRUD(router, 'tipo-movimiento', TipoMovimientoQuery(), TipoMovimiento, TipoMovimientoCreate)
CRUD(router, 'estado', EstadoVarianteQuery(), EstadoVariante, EstadoVarianteCreate)
CRUD(router, 'metavalor', MetaValorQuery(), MetaValor, MetaValorCreate)
CRUD(router, 'metaatributo', MetaAtributoQuery(), MetaAtributo, MetaValorCreate)


@router.get(
    '/movimmiento-with-relations',
    status_code=status.HTTP_200_OK,
    response_model=list[MovimientoRead],
    summary='Obtiene una lista de movimientos con relaciones',
    description='Obtiene una lista paginada de movimientos con sus relaciones cargadas y opcionalmente filtrados por rango de fechas.',
    tags=[Tags.INVENTARIO],
    dependencies=[Depends(validar_access_token)],
)
async def get_movimientos_with_relations(
    session: AsyncSessionDep,
    start_date: date,
    end_date: date,
    sort: Sort = Sort.DESC,
):
    movimiento_query = MovimientoQuery()
    movimientos = await movimiento_query.get_with_relations(
        session=session,
        sort=sort,
        start_date=start_date,
        end_date=end_date,
    )
    return movimientos


class Frequency(str, Enum):
    DAILY = 'D'
    WEEKLY = 'W'
    MONTHLY = 'ME'
    YEARLY = 'Y'


class GroupByMovimientos(str, Enum):
    BODEGA = 'bodega_id'
    VARIANTE = 'variante_id'
    META_ATRIBUTO = 'meta_atributo'
    META_VALOR = 'meta_valor'


class GroupByLikeMetaValor(str, Enum):
    BODEGA = 'bodega_id'
    VARIANTE = 'variante_id'


class FiltroTipoMovimiento(str, Enum):
    SALIDA = 'salida'
    ENTRADA = 'entrada'
    AUMENTO = 'aumento'
    DISMINUCION = 'disminucion'
    CARGUE_INICIAL = 'cargue inicial'


class FiltroTipoSoporte(str, Enum):
    COMPRA = 'factura de compra'
    PEDIDO = 'pedido'
    VENTA = 'venta'
    TRASLADO = 'traslado'

class GroupByLike(BaseModel):
    group_by: set[GroupByLikeMetaValor]


@router.get(
    '/metadatos-distinct',
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(validar_access_token)],
)
async def get_meta_datos_distinct(session: AsyncSessionDep):
    return await MetadatosPorSoporteQuery().get_distinct(session)

class BodyMovimientoAgrupados(BaseModel):
    group_by: set[GroupByMovimientos] = {GroupByMovimientos.VARIANTE}
    meta_valor_ids: list[int] | None = None

# region reportes
@router.post(
    '/movimientos-agrupados',
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(validar_access_token)],
)
async def get_movimientos_agrupados(
    session: AsyncSessionDep,
    start_date: date,
    end_date: date,
    sort: Sort = Sort.DESC,
    frequency: Frequency = Frequency.DAILY,
    filtro_tipo_movimiento: FiltroTipoMovimiento | None = None,
    filtro_tipo_soporte: FiltroTipoSoporte | None = None,
    body: BodyMovimientoAgrupados = BodyMovimientoAgrupados(),
):
    tipo_movimiento_id = None
    tipo_soporte_id = None
    if filtro_tipo_movimiento:
        tipo_movimiento = await TipoMovimientoQuery().get_by_nombre(session, filtro_tipo_movimiento.value)
        if not tipo_movimiento:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Tipo de movimiento no encontrado')
        tipo_movimiento_id = tipo_movimiento.id
    if filtro_tipo_soporte:
        tipo_soporte = await TipoSoporteQuery().get_by_nombre(session, filtro_tipo_soporte.value)
        if not tipo_soporte:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Tipo de soporte no encontrado')
        tipo_soporte_id = tipo_soporte.id

    movimientos = await MovimientoQuery().get_by_dates(
        session=session,
        start_date=start_date,
        end_date=end_date,
        sort=sort,
        tipo_movimiento_id=tipo_movimiento_id,
        tipo_soporte_id=tipo_soporte_id,
    )

    if not movimientos:
        return []

    df_movimientos = DataFrame([mov.model_dump() for mov in movimientos])
    df = df_movimientos.copy()

    metadatos = None
    meta_agrupadores = {GroupByMovimientos.META_ATRIBUTO, GroupByMovimientos.META_VALOR} & body.group_by
    if tipo_soporte_id and meta_agrupadores:
        metadatos = await MetadatosPorSoporteQuery().get_list_by(
            session=session,
            tipo_soporte_id=tipo_soporte_id,
            meta_valor_ids=body.meta_valor_ids,
            soporte_ids=[movimiento.soporte_id for movimiento in movimientos if movimiento.soporte_id],
        )

    if meta_agrupadores and not tipo_soporte_id:
        for meta_agrupador in meta_agrupadores:
            body.group_by.remove(meta_agrupador)

    if metadatos:
        df_metadatos = DataFrame(metadatos)
        df = df.merge(df_metadatos, left_on='soporte_id', right_on='soporte_id', how='inner')

    if df.empty:
        return []

    df = (
        df.set_index('fecha')
        .groupby([Grouper(freq=frequency.value), 'tipo_movimiento_id', *body.group_by])
        .agg(
            {
                'cantidad': 'sum',
                'valor': 'sum',
            }
        )
        .reset_index()
    )

    total_cantidad = df['cantidad'].sum()
    df['cantidad_%'] = df['cantidad'] / total_cantidad * 100

    total_valor = df['valor'].sum()
    df['valor_%'] = df['valor'] / total_valor * 100

    if GroupByMovimientos.VARIANTE in body.group_by:
        variantes_elemento = await VarianteElementoQuery().get_list(session)

        df_variantes = DataFrame([ve.model_dump() for ve in variantes_elemento])

        df = df.merge(df_variantes, left_on='variante_id', right_on='id', how='left')
        df = df.drop(columns=['id', 'variante_id', 'shopify_id'])
        df = df.rename(columns={'nombre': 'variante'})

    if GroupByMovimientos.BODEGA in body.group_by:
        bodegas = await BodegaQuery().get_list(session)
        df_bodegas = DataFrame([bodega.model_dump() for bodega in bodegas])
        df = df.merge(df_bodegas, left_on='bodega_id', right_on='id', how='left')
        df = df.drop(columns=['id', 'bodega_id', 'shopify_id'])

    return df.to_dict(orient='records')


class BodyMovimientoAgrupadosLikeMetaValor(BaseModel):
    group_by: set[GroupByLikeMetaValor] = {GroupByLikeMetaValor.VARIANTE}

@router.post(
    'movimientos-agrupados-like-metavalor',
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(validar_access_token)],
)
async def get_movimientos_agrupados_like_metavalor(
    session: AsyncSessionDep,
    start_date: date,
    end_date: date,
    filtro_tipo_soporte: FiltroTipoSoporte,
    like_metavalor: str,
    frequency: Frequency = Frequency.DAILY,
    sort: Sort = Sort.DESC,
    filtro_tipo_movimiento: FiltroTipoMovimiento | None = None,
    body: BodyMovimientoAgrupadosLikeMetaValor = BodyMovimientoAgrupadosLikeMetaValor(),
):
    tipo_movimiento_id = None
    tipo_soporte_id = None
    if filtro_tipo_movimiento:
        tipo_movimiento = await TipoMovimientoQuery().get_by_nombre(session, filtro_tipo_movimiento.value)
        if not tipo_movimiento:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Tipo de movimiento no encontrado')
        tipo_movimiento_id = tipo_movimiento.id
    if filtro_tipo_soporte:
        tipo_soporte = await TipoSoporteQuery().get_by_nombre(session, filtro_tipo_soporte.value)
        if not tipo_soporte:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Tipo de soporte no encontrado')
        tipo_soporte_id = tipo_soporte.id

    if not tipo_soporte_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Tipo de soporte no encontrado')

    movimientos = await MovimientoQuery().get_by_dates(
        session=session,
        start_date=start_date,
        end_date=end_date,
        sort=sort,
        tipo_movimiento_id=tipo_movimiento_id,
        tipo_soporte_id=tipo_soporte_id,
    )

    if not movimientos:
        return []

    df_movimientos = DataFrame([mov.model_dump() for mov in movimientos])

    metadatos = None
    metadatos = await MetadatosPorSoporteQuery().get_like(
        session=session,
        tipo_soporte_id=tipo_soporte_id,
        meta_valor=like_metavalor,
    )
    if not metadatos:
        return []

    df = df_movimientos.merge(DataFrame(metadatos), left_on='soporte_id', right_on='soporte_id', how='inner')

    df = (
        df.set_index('fecha')
        .groupby([Grouper(freq=frequency.value), 'meta_valor', *body.group_by])
        .agg(
            {
                'cantidad': 'sum',
                'valor': 'sum',
            }
        )
        .reset_index()
    )

    total_cantidad = df['cantidad'].sum()
    df['cantidad_%'] = df['cantidad'] / total_cantidad * 100

    total_valor = df['valor'].sum()
    df['valor_%'] = df['valor'] / total_valor * 100

    if GroupByMovimientos.VARIANTE in body.group_by:
        variantes_elemento = await VarianteElementoQuery().get_list(session)

        df_variantes = DataFrame([ve.model_dump() for ve in variantes_elemento])

        df = df.merge(df_variantes, left_on='variante_id', right_on='id', how='left')
        df = df.drop(columns=['id', 'variante_id', 'shopify_id'])
        df = df.rename(columns={'nombre': 'variante'})

    if GroupByMovimientos.BODEGA in body.group_by:
        bodegas = await BodegaQuery().get_list(session)
        df_bodegas = DataFrame([bodega.model_dump() for bodega in bodegas])
        df = df.merge(df_bodegas, left_on='bodega_id', right_on='id', how='left')
        df = df.drop(columns=['id', 'bodega_id', 'shopify_id'])

    return df.to_dict(orient='records')


@router.get(
    '/saldos',
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(validar_access_token)],
)
async def get_saldos(session: AsyncSessionDep):
    movimiento_query = MovimientoQuery()
    saldos = await movimiento_query.get_saldos(session)
    return saldos


CRUD(router, 'movimiento', MovimientoQuery(), Movimiento, MovimientoCreate)
# endregion reportes


# Pedidos
@shopify_inventario_router.post(
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
    # Obtener datos de pedido
    order_webhook = OrderWebHook(**request_json)
    """Se evidencia que shopify en ocasiones intenta enviar el mismo pedido varias veces.
    Se evita usando BackgroundTasks pos si es a causa de un TimeoutError."""
    background_tasks.add_task(procesar_pedido_shopify, order_webhook.order_number, order_webhook.admin_graphql_api_id)

    return True


# Sincronización
@shopify_inventario_router.post(
    '/sync-shopify',
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
        await ShopifyInventario().sicnronizar_inventario(True)
        return True
    except Exception as e:
        log_inventario_shopify.error(f'Error al sincronizar inventarios de Shopify: {e}')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@shopify_inventario_router.post(
    '/sync-movimientos-ordenes-by-range',
    status_code=status.HTTP_200_OK,
    tags=[Tags.INVENTARIO, Tags.SHOPIFY],
    dependencies=[Depends(validar_access_token)],
)
async def sync_movimientos_ordenes_by_range(date_range: DateRange, background_tasks: BackgroundTasks):
    background_tasks.add_task(
        ShopifyInventario().sincronizar_movimientos_ordenes_by_range,
        date_range.start_date,
        date_range.end_date,
    )
    return True


@shopify_inventario_router.post(
    '/sync-metadata-ordenes-by-range',
    status_code=status.HTTP_200_OK,
    tags=[Tags.INVENTARIO, Tags.SHOPIFY],
    dependencies=[Depends(validar_access_token)],
)
async def sync_metadata_ordenes_by_range(date_range: DateRange, background_tasks: BackgroundTasks):
    background_tasks.add_task(
        ShopifyInventario().crear_metadata_orders_by_range,
        date_range.start_date,
        date_range.end_date,
    )
    return True


if __name__ == '__main__':
    from asyncio import run
    from app.models.db.session import get_async_session

    async def main():
        async for session in get_async_session():
            async with session:
                records = await get_movimientos_agrupados(
                    session=session,
                    start_date=date(2025, 9, 1),
                    end_date=date(2025, 9, 30),
                    sort=Sort.DESC,
                    frequency=Frequency.MONTHLY,
                    filtro_tipo_soporte=FiltroTipoSoporte.PEDIDO,
                    filtro_tipo_movimiento=FiltroTipoMovimiento.SALIDA,
                    body=BodyMovimientoAgrupados()
                )
                df = DataFrame(records)
                print(df)

                # await get_movimientos_agrupados_like_metavalor(
                #     session=session,
                #     start_date=date(2025, 9, 1),
                #     end_date=date(2025, 9, 30),
                #     sort=Sort.DESC,
                #     frequency=Frequency.MONTHLY,
                #     like_metavalor='keila',
                #     filtro_tipo_soporte=FiltroTipoSoporte.PEDIDO,
                #     filtro_tipo_movimiento=FiltroTipoMovimiento.SALIDA,
                # )
                # df = DataFrame(records)
                # print(df)

    run(main())
