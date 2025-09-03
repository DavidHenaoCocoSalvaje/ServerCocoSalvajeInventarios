# app/routers/inventario.py
from enum import Enum
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request, status


from app.internal.integrations.shopify import ShopifyGraphQLClient, persistir_inventory_info
from app.models.pydantic.shopify.order import OrderWebHook
from app.routers.base import CRUD
from app.internal.log import LogLevel, factory_logger

# Seguridad
from app.routers.auth import hmac_validation_shopify

# Facturacion

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
from app.routers.auth import validar_access_token
from app.routers.ul.ul_inventario import procesar_pedido_shopify

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
    shopify_client = ShopifyGraphQLClient()
    # Obtener datos de pedido
    order_webhook = OrderWebHook(**request_json)
    # Se consulta la orden porque la información que viene del webhook no incluye la información de la transacción.
    try:
        order_response = await shopify_client.get_order(order_webhook.admin_graphql_api_id)
    except Exception as e:
        # No se lanza excepción porque es un webhook, se registra únicamente en el log y se responde Ok para no recibir el mismo webhook.
        log_inventario_shopify.error(str(e))
        return True

    if order_response.data.order is None:
        log_inventario_shopify.error(f'Order not found: {order_response.model_dump_json()}')
    order = order_response.data.order

    """Se evidencia que shopify en ocasiones intenta enviar el mismo pedido varias veces.
    Se evita usando BackgroundTasks pos si es a causa de un TimeoutError."""
    background_tasks.add_task(procesar_pedido_shopify, order)

    return True
