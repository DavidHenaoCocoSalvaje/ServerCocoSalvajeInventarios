# app/routers/inventario.py
from dataclasses import dataclass
from fastapi import APIRouter, Depends, status
from app.internal.integrations.shopify import get_inventory_info
from app.routers.base import CRUD


# Modelos


from app.models.db.inventario import (
    Bodega,
    ElementoCompuesto,
    Elemento,
    Grupo,
    TipoMovimiento,
    TipoPrecioVariante,
    VariantesPorElementoCompuesto,
    PreciosPorVariante,
    Movimiento,
    EstadoElemento,
    UnidadMedida,
)

# Base de datos (Repositorio)
from app.internal.query.inventario import (
    bodega_inventario_query,
    grupo_inventario_query,
    elemento_inventario_query,
    unidad_medida_query,
    elemento_compuesto_inventario_query,
    elementos_por_elemento_compuesto_inventario_query,
    precio_elemento_inventario_query,
    tipo_precio_elemento_inventario_query,
    movimiento_inventario_query,
    tipo_movimiento_inventario_query,
    estado_elemento_inventario_query,
)
from .auth import validar_access_token


@dataclass
class Tags:
    shopify: str = "Shopify"


router = APIRouter(
    prefix="/inventario",
    tags=["Inventario"],
    responses={404: {"description": "No encontrado"}},
    dependencies=[Depends(validar_access_token)],
)


# Llamadas a la función genérica para cada modelo de inventario
CRUD[Elemento](
    router,
    elemento_inventario_query,
    "elemento",
)

CRUD[ElementoCompuesto](
    router,
    elemento_compuesto_inventario_query,
    "elemento_compuesto",
)
CRUD[VariantesPorElementoCompuesto](
    router,
    elementos_por_elemento_compuesto_inventario_query,
    "elementos_por_elemento_compuesto",
)
CRUD[Bodega](
    router,
    bodega_inventario_query,
    "bodega",
)
CRUD[Grupo](
    router,
    grupo_inventario_query,
    "grupo",
)
CRUD[UnidadMedida](
    router,
    unidad_medida_query,
    "unidad_medida",
)
CRUD[PreciosPorVariante](
    router,
    precio_elemento_inventario_query,
    "precio",
)
CRUD[TipoPrecioVariante](
    router,
    tipo_precio_elemento_inventario_query,
    "tipo_precio",
)
CRUD[Movimiento](
    router,
    movimiento_inventario_query,
    "movimiento",
)
CRUD[TipoMovimiento](
    router,
    tipo_movimiento_inventario_query,
    "tipo_movimiento",
)
CRUD[EstadoElemento](
    router,
    estado_elemento_inventario_query,
    "estado",
)


# Sincronización
@router.post(
    "/sync_shopify",
    response_model=bool,
    summary="Sincroniza inventarios de Shopify con base de datos",
    description="Se registran movimiento de cargue.",
    status_code=status.HTTP_200_OK,
    tags=[Tags.shopify],
)
async def sync_shopify(body: dict):
    # Obtener información inventario de shopify
    inventory_info = await get_inventory_info()
    # Obtener lista de bodegas y filtrar por registros únicos, luego verificar si es necesario crear alguna bodega
    locations = []
    for product in inventory_info:
        for variant in product.variants:
            for inventory_level in variant.inventoryItem.inventoryLevels.nodes:
                location = inventory_level.location
                locations.append(location)

    return {"message": "Inventarios sincronizado con Shopify"}
