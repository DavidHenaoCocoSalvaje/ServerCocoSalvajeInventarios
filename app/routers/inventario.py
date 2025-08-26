# app/routers/inventario.py
from enum import Enum
from re import A
from typing import Awaitable, Callable
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.internal.integrations.shopify import QueryShopify, get_inventory_info, persistir_inventory_info
from app.models.db.transacciones import Accion, PedidoCreate
from app.models.db.session import AsyncSessionDep
from app.models.pydantic.shopify.order import Order, OrderResponse, OrderWebHook
from app.models.pydantic.world_office.facturacion import WODocumentoVentaCreate
from app.routers.base import CRUD
from app.internal.log import LogLevel, factory_logger

# Seguridad
from app.routers.auth import hmac_validation_shopify


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
from .auth import validar_access_token

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
        inventory_info = await get_inventory_info()
        await persistir_inventory_info(inventory_info)
        log_inventario_shopify.info('Inventarios de Shopify sincronizado con éxito')
        return True
    except Exception as e:
        log_inventario_shopify.error(f'Error al sincronizar inventarios de Shopify: {e}')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Pedidos
@shopify_router.post(
    '/pedido',
    status_code=status.HTTP_200_OK,
    tags=[Tags.INVENTARIO, Tags.SHOPIFY],
    dependencies=[Depends(hmac_validation_shopify)],
)
async def procesar_pedido_shopify(request: Request, session: AsyncSessionDep):
    query_shopify = QueryShopify()
    # Obtener datos de pedido
    webhook_data = await request.json()
    order_webhook = OrderWebHook(**webhook_data)
    # Se consulta la orden porque la ingormación que viene del webhook no incluye la información de la transacción.
    order = await query_shopify.get_order(order_webhook.admin_graphql_api_id)
    order_response = OrderResponse(**order)
    log_inventario_shopify.info(f'\nPedido recibido: {order_response.model_dump_json()}')
    if order_response.data.order is None:
        log_inventario_shopify.error(f'Order not found: {order_response.model_dump_json()}')
    order = order_response.data.order


async def facturar_pedido(order: Order, session: AsyncSessionDep):
    if not order.fullyPaid:
        # Se crea pedido porque se notifico dsede shopify, pero como no tiene pago aún no se factura.
        pedido_create = PedidoCreate(numero=str(order.number), acccion=Accion.CREAR)
        await pedido_query.create(session, pedido_create)
        # pedido_query.create(session, Pedido(acccion=Accion.FACTURAR, order=order.id))
        return

    # Si los pagos son por wompi (contado), si son por addi (pse: contado, credito: credito, por defecto se deja en crédito)
    # 4 para contado, 5 para credito

    # Verificar que todos sean womopi con all
    id_forma_pago = 5
    # if all(x.gateway == 'Addi Payment' for x in order.transactions):

    factura_create = WODocumentoVentaCreate(
        prefijo=1,  # Sin prefijo
        documentoTipo='FV',
        concepto='Prueba API',
        idEmpresa=1,
        idTerceroExterno=1,
        idFormaPago=1,
    )
