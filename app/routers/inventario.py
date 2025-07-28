# app/routers/inventario.py
from fastapi import APIRouter, Depends
from app.routers.base import CRUD

# Modelos


from app.models.inventario import (
    BodegaInventario,
    ElementoCompuestoInventario,
    ElementoInventario,
    GrupoInventario,
    TipoMovimientoInventario,
    TipoPrecioElementoInventario,
    ElementosPorElementoCompuestoInventario,
    PrecioElementoInventario,
    MovimientoInventario,
    EstadoElementoInventario,
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

router = APIRouter(
    prefix="/inventario",
    tags=["Inventario"],
    responses={404: {"description": "No encontrado"}},
    dependencies=[Depends(validar_access_token)],
)


# Llamadas a la función genérica para cada modelo de inventario
CRUD[ElementoInventario](
    router,
    elemento_inventario_query,
    "elemento",
)

CRUD[ElementoCompuestoInventario](
    router,
    elemento_compuesto_inventario_query,
    "elemento_compuesto",
)
CRUD[ElementosPorElementoCompuestoInventario](
    router,
    elementos_por_elemento_compuesto_inventario_query,
    "elementos_por_elemento_compuesto",
)
CRUD[BodegaInventario](
    router,
    bodega_inventario_query,
    "bodega",
)
CRUD[GrupoInventario](
    router,
    grupo_inventario_query,
    "grupo",
)
CRUD[UnidadMedida](
    router,
    unidad_medida_query,
    "unidad_medida",
)
CRUD[PrecioElementoInventario](
    router,
    precio_elemento_inventario_query,
    "precio",
)
CRUD[TipoPrecioElementoInventario](
    router,
    tipo_precio_elemento_inventario_query,
    "tipo_precio",
)
CRUD[MovimientoInventario](
    router,
    movimiento_inventario_query,
    "movimiento",
)
CRUD[TipoMovimientoInventario](
    router,
    tipo_movimiento_inventario_query,
    "tipo_movimiento",
)
CRUD[EstadoElementoInventario](
    router,
    estado_elemento_inventario_query,
    "estado",
)
