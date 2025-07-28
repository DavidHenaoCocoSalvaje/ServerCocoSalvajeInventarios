# app/routers/inventario.py
from fastapi import APIRouter, Depends
from app.routers.base import create_crud_routes

# Modelos


from app.models.inventario import (
    BodegaInventarioResponse,
    ElementoCompuestoInventarioResponse,
    ElementoInventarioResponse,
    GrupoInventarioResponse,
    TipoMovimientoInventarioResponse,
    TipoPrecioElementoInventarioResponse,
    ElementosPorElementoCompuestoInventario,
    PrecioElementoInventarioResponse,
    MovimientoInventarioResponse,
    EstadoElementoInventarioResponse,
    UnidadMedidaResponse,
)

# Base de datos (Repositorio)
from app.internal.query.inventario import (
    BodegaInventarioQuery,
    GrupoInventarioQuery,
    ElementoInventarioQuery,
    UnidadMedidaQuery,
    ElementoCompuestoInventarioQuery,
    ElementosPorElementoCompuestoInventarioQuery,
    PrecioElementoInventarioQuery,
    TipoPrecioElementoInventarioQuery,
    MovimientoInventarioQuery,
    TipoMovimientoInventarioQuery,
    EstadoElementoInventarioQuery,
)
from .auth import validar_access_token

router = APIRouter(
    prefix="/inventario",
    tags=["Inventario"],
    responses={404: {"description": "No encontrado"}},
    dependencies=[Depends(validar_access_token)],
)


# Llamadas a la función genérica para cada modelo de inventario
create_crud_routes(
    router,
    ElementoInventarioResponse,
    ElementoInventarioQuery,
    "elemento",
)
create_crud_routes(
    router,
    ElementoCompuestoInventarioResponse,
    ElementoCompuestoInventarioQuery,
    "elemento_compuesto",
)
create_crud_routes(
    router,
    ElementosPorElementoCompuestoInventario,
    ElementosPorElementoCompuestoInventarioQuery,
    "elementos_por_elemento_compuesto",
)
create_crud_routes(
    router,
    PrecioElementoInventarioResponse,
    PrecioElementoInventarioQuery,
    "precio",
)
create_crud_routes(
    router,
    TipoPrecioElementoInventarioResponse,
    TipoPrecioElementoInventarioQuery,
    "tipo_precio",
)
create_crud_routes(
    router,
    BodegaInventarioResponse,
    BodegaInventarioQuery,
    "bodega",
)
create_crud_routes(
    router,
    GrupoInventarioResponse,
    GrupoInventarioQuery,
    "grupo",
)
create_crud_routes(
    router,
    MovimientoInventarioResponse,
    MovimientoInventarioQuery,
    "movimiento",
)
create_crud_routes(
    router,
    TipoMovimientoInventarioResponse,
    TipoMovimientoInventarioQuery,
    "tipo_movimiento",
    id_type=int,
)  # Asegúrate de que el tipo de ID sea correcto
create_crud_routes(
    router,
    EstadoElementoInventarioResponse,
    EstadoElementoInventarioQuery,
    "estado",
)
create_crud_routes(
    router,
    UnidadMedidaResponse,
    UnidadMedidaQuery,
    "unidad_medida",
)
