# app/routers/inventario.py
from fastapi import APIRouter, Depends
from app.routers.base import create_crud_routes

# Modelos


from app.models.inventario import (
    BodegaInventario,
    GrupoInventario,
    UnidadMedida,
    ElementoInventario,
    ElementoCompuestoInventario,
    ElementosPorElementoCompuestoInventario,
    PrecioElementoInventario,
    TipoPrecioElementoInventario,
    MovimientoInventario,
    TipoMovimientoInventario,
    EstadoElementoInventario,
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
    router, ElementoInventario, ElementoInventarioQuery, "elemento_inventario"
)
create_crud_routes(
    router,
    ElementoCompuestoInventario,
    ElementoCompuestoInventarioQuery,
    "elemento_compuesto_inventario",
)
create_crud_routes(
    router,
    ElementosPorElementoCompuestoInventario,
    ElementosPorElementoCompuestoInventarioQuery,
    "elementos_por_elemento_compuesto_inventario",
)
create_crud_routes(
    router,
    PrecioElementoInventario,
    PrecioElementoInventarioQuery,
    "precio_elemento_inventario",
)
create_crud_routes(
    router,
    TipoPrecioElementoInventario,
    TipoPrecioElementoInventarioQuery,
    "tipo_precio_elemento_inventario",
)
create_crud_routes(router, BodegaInventario, BodegaInventarioQuery, "bodega_inventario")
create_crud_routes(router, GrupoInventario, GrupoInventarioQuery, "grupo_inventario")
create_crud_routes(
    router, MovimientoInventario, MovimientoInventarioQuery, "movimiento_inventario"
)
create_crud_routes(
    router,
    TipoMovimientoInventario,
    TipoMovimientoInventarioQuery,
    "tipo_movimiento_inventario",
    id_type=int,
)  # Asegúrate de que el tipo de ID sea correcto
create_crud_routes(
    router,
    EstadoElementoInventario,
    EstadoElementoInventarioQuery,
    "estado_elemento_inventario",
)
create_crud_routes(router, UnidadMedida, UnidadMedidaQuery, "unidad_medida")
