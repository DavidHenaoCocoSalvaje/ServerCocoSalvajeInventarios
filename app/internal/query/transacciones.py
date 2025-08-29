# app.internal.query.transacciones
from app.internal.query.base import BaseQuery
from app.models.db.transacciones import (
    Pedido,
    PedidoCreate,
)

from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession


class PedidoQuery(BaseQuery[Pedido, PedidoCreate]):
    def __init__(self) -> None:
        super().__init__(Pedido, PedidoCreate)

    async def get_by_number(self, session: AsyncSession, order_number: int) -> Pedido | None:
        statement = select(self.model_db).where(self.model_db.numero == order_number)
        result = await session.execute(statement)
        return result.scalar_one_or_none()


pedido_query = PedidoQuery()
