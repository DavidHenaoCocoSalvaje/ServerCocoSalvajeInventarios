# app/routers/inventario.py
from enum import Enum
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request, status


from app.internal.integrations.shopify import ShopifyGraphQLClient, persistir_inventory_info
from app.internal.query.inventario import (
    BodegaQuery,
    ComponentesPorVarianteQuery,
    ElementoQuery,
    EstadoVarianteQuery,
    GrupoQuery,
    MedidaQuery,
    MedidasPorVarianteQuery,
    MovimientoQuery,
    PrecioPorVarianteQuery,
    TipoMovimientoQuery,
    TipoPrecioQuery,
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
    Movimiento,
    MovimientoCreate,
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

shopify_router = APIRouter(
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
CRUD(router, 'unidad_medida', MedidaQuery(), Medida, MedidaCreate)
CRUD(router, 'precio', PrecioPorVarianteQuery(), PreciosPorVariante, PreciosPorVarianteCreate)
CRUD(router, 'tipo_precio', TipoPrecioQuery(), TipoPrecio, TipoPrecioCreate)
CRUD(router, 'tipo_medida', TiposMedidaQuery(), TiposMedida, TiposMedidaCreate)
CRUD(router, 'medida', MedidasPorVarianteQuery(), MedidasPorVariante, MedidasPorVarianteCreate)
CRUD(router, 'movimiento', MovimientoQuery(), Movimiento, MovimientoCreate)
CRUD(router, 'tipo_movimiento', TipoMovimientoQuery(), TipoMovimiento, TipoMovimientoCreate)
CRUD(router, 'estado', EstadoVarianteQuery(), EstadoVariante, EstadoVarianteCreate)


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
        inventory_info = await shopify_client.get_inventory_info()
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
    # Obtener datos de pedido
    order_webhook = OrderWebHook(**request_json)
    """Se evidencia que shopify en ocasiones intenta enviar el mismo pedido varias veces.
    Se evita usando BackgroundTasks pos si es a causa de un TimeoutError."""
    background_tasks.add_task(procesar_pedido_shopify, order_webhook.order_number, order_webhook.admin_graphql_api_id)

    return True
