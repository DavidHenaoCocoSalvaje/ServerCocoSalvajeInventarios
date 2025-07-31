# app/internal/query/inventario.py
from app.models.inventario import (
    Elemento,
    ElementoCompuesto,
    VariantesPorElementoCompuesto,
    Bodega,
    Grupo,
    UnidadMedida,
    PreciosPorVariante,
    TipoPrecioVariante,
    Movimiento,
    TipoMovimiento,
    EstadoElemento,
)
from app.internal.query.base import BaseQuery


elemento_inventario_query = BaseQuery(Elemento)
elemento_compuesto_inventario_query = BaseQuery(ElementoCompuesto)
elementos_por_elemento_compuesto_inventario_query = BaseQuery(
    VariantesPorElementoCompuesto
)
bodega_inventario_query = BaseQuery(Bodega)
grupo_inventario_query = BaseQuery(Grupo)
unidad_medida_query = BaseQuery(UnidadMedida)
precio_elemento_inventario_query = BaseQuery(PreciosPorVariante)
tipo_precio_elemento_inventario_query = BaseQuery(TipoPrecioVariante)
movimiento_inventario_query = BaseQuery(Movimiento)
tipo_movimiento_inventario_query = BaseQuery(TipoMovimiento)
estado_elemento_inventario_query = BaseQuery(EstadoElemento)
