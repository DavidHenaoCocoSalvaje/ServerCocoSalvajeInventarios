# app/routers/inventario.py
from dataclasses import dataclass
import json
from fastapi import APIRouter, Depends, HTTPException, status, Response

from app.internal.integrations.shopify import get_inventory_info, process_inventory_info
from app.routers.base import CRUD
from app.internal.log import factory_logger

# Modelos


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
from .auth import validar_access_token

log_inventario = factory_logger('inventario', file=True)
log_inventario_shopify = factory_logger('inventario_shopify', file=True)


@dataclass
class Tags:
    inventario: str = 'Inventario'
    shopify: str = 'Shopify'


router = APIRouter(
    prefix='/inventario',
    tags=[Tags.inventario],
    responses={404: {'description': 'No encontrado'}},
    dependencies=[Depends(validar_access_token)],
)

shopify_router = APIRouter(
    prefix='/inventario/shopify',
    tags=[Tags.inventario, Tags.shopify],
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
    tags=[Tags.inventario, Tags.shopify],
)
async def sync_shopify(response: Response):
    """Sincroniza los datos de inventario desde Shopify."""
    try:
        # Obtener información inventario de shopify
        inventory_info = await get_inventory_info()
        await process_inventory_info(inventory_info)
        log_inventario_shopify.info('Inventarios de Shopify sincronizado con éxito')
        return True
    except Exception as e:
        log_inventario_shopify.error(f'Error al sincronizar inventarios de Shopify: {e}')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Pedidos
@shopify_router.post(
    '/pedido',
    status_code=status.HTTP_200_OK,
    tags=[Tags.inventario, Tags.shopify],
)
async def pedido_shopify(body: dict):
    log_inventario.info(f'\nPedido recibido: {json.dumps(body, indent=4)}')
    return {'status': 'ok'}
