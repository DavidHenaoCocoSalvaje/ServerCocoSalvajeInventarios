# app/routers/inventario.py
from fastapi import APIRouter, Depends
from app.routers.base import FabricCRUD

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
elemento_inventario_crud_fabric = FabricCRUD[ElementoInventarioResponse]()
elemento_inventario_crud_fabric.create_crud_routes(
    router,
    elemento_inventario_query,
    "elemento",
)
elemento_compuesto_crud_fabric = FabricCRUD[ElementoCompuestoInventarioResponse]()
elemento_compuesto_crud_fabric.create_crud_routes(
    router,
    elemento_compuesto_inventario_query,
    "elemento_compuesto",
)
elementos_por_elemento_compuesto_crud_fabric = FabricCRUD[
    ElementosPorElementoCompuestoInventario
]()
elementos_por_elemento_compuesto_crud_fabric.create_crud_routes(
    router,
    elementos_por_elemento_compuesto_inventario_query,
    "elementos_por_elemento_compuesto",
)
bodega_inventario_crud_fabric = FabricCRUD[BodegaInventarioResponse]()
bodega_inventario_crud_fabric.create_crud_routes(
    router,
    bodega_inventario_query,
    "bodega",
)
grupo_inventario_crud_fabric = FabricCRUD[GrupoInventarioResponse]()
grupo_inventario_crud_fabric.create_crud_routes(
    router,
    grupo_inventario_query,
    "grupo",
)
unidad_medida_crud_fabric = FabricCRUD[UnidadMedidaResponse]()
unidad_medida_crud_fabric.create_crud_routes(
    router,
    unidad_medida_query,
    "unidad_medida",
)
precio_elemento_inventario_crud_fabric = FabricCRUD[PrecioElementoInventarioResponse]()
precio_elemento_inventario_crud_fabric.create_crud_routes(
    router,
    precio_elemento_inventario_query,
    "precio",
)
tipo_precio_elemento_inventario_crud_fabric = FabricCRUD[
    TipoPrecioElementoInventarioResponse
]()
tipo_precio_elemento_inventario_crud_fabric.create_crud_routes(
    router,
    tipo_precio_elemento_inventario_query,
    "tipo_precio",
)
movimiento_inventario_crud_fabric = FabricCRUD[MovimientoInventarioResponse]()
movimiento_inventario_crud_fabric.create_crud_routes(
    router,
    movimiento_inventario_query,
    "movimiento",
)
tipo_movimiento_inventario_crud_fabric = FabricCRUD[TipoMovimientoInventarioResponse]()
tipo_movimiento_inventario_crud_fabric.create_crud_routes(
    router,
    tipo_movimiento_inventario_query,
    "tipo_movimiento",
)
estado_elemento_inventario_crud_fabric = FabricCRUD[EstadoElementoInventarioResponse]()
estado_elemento_inventario_crud_fabric.create_crud_routes(
    router,
    estado_elemento_inventario_query,
    "estado",
)
