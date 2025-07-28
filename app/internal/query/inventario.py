# app/internal/query/inventario.py
from app.models.inventario import (
    ElementoInventario,
    ElementoCompuestoInventario,
    ElementosPorElementoCompuestoInventario,
    BodegaInventario,
    GrupoInventario,
    UnidadMedida,
    PrecioElementoInventario,
    TipoPrecioElementoInventario,
    MovimientoInventario,
    TipoMovimientoInventario,
    EstadoElementoInventario,
)
from app.internal.query.base import BaseQuery


elemento_inventario_query = BaseQuery(ElementoInventario)
elemento_compuesto_inventario_query = BaseQuery(ElementoCompuestoInventario)
elementos_por_elemento_compuesto_inventario_query = BaseQuery(
    ElementosPorElementoCompuestoInventario
)
bodega_inventario_query = BaseQuery(BodegaInventario)
grupo_inventario_query = BaseQuery(GrupoInventario)
unidad_medida_query = BaseQuery(UnidadMedida)
precio_elemento_inventario_query = BaseQuery(PrecioElementoInventario)
tipo_precio_elemento_inventario_query = BaseQuery(TipoPrecioElementoInventario)
movimiento_inventario_query = BaseQuery(MovimientoInventario)
tipo_movimiento_inventario_query = BaseQuery(TipoMovimientoInventario)
estado_elemento_inventario_query = BaseQuery(EstadoElementoInventario)
