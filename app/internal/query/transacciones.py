# app.internal.query.transacciones

from app.internal.query.base import BaseQuery
from app.models.db.transacciones import (
    Pedido,
    PedidoCreate,
)

pedido_query = BaseQuery(Pedido, PedidoCreate)
