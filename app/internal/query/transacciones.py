# app.internal.query.transacciones
from datetime import timedelta
from app.internal.gen.utilities import DateTz
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

    async def get_pendientes_facturar(self, session: AsyncSession) -> list[Pedido]:
        # factura_id = '' o q_intentos > 0
        # Se restan 5 minutos para evitar obtener pedidos que se están procesando en el momento.
        datetime = DateTz.local() - timedelta(minutes=5)
        statement = (
            select(self.model_db)
            .where(not self.model_db.contabilizado)
            .where(self.model_db.q_intentos > 0)
            .where(self.model_db.fecha < datetime)
        )
        result = await session.execute(statement)
        return list(result.scalars().all()) or []
