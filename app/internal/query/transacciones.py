# app.internal.query.transacciones

from datetime import timedelta
from typing import TypeVar
from app.internal.gen.utilities import DateTz

from app.internal.query.base import BaseQuery
from app.models.db.transacciones import (
    Compra,
    CompraCreate,
    Pedido,
    PedidoCreate,
    TransaccionBase,
)

from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession


ModelDB = TypeVar('ModelDB', bound=TransaccionBase)
ModelCreate = TypeVar('ModelCreate', bound=TransaccionBase)


# region legacy
class PedidoQuery(BaseQuery[Pedido, PedidoCreate]):
    def __init__(self) -> None:
        super().__init__(Pedido, PedidoCreate)

    async def get_by_number(self, session: AsyncSession, order_number: int) -> Pedido | None:
        statement = select(self.model_db).where(self.model_db.numero == order_number)
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_numbers(self, session: AsyncSession, order_numbers: list[int]) -> list[Pedido]:
        statement = select(self.model_db).where(self.model_db.numero.in_(order_numbers))  # type: ignore
        result = await session.execute(statement)
        return list(result.scalars().all())

    async def get_pendientes_facturar(self, session: AsyncSession) -> list[Pedido]:
        # factura_id = '' o q_intentos > 0
        # Se restan 5 minutos para evitar obtener pedidos que se están procesando en el momento.
        datetime = DateTz.local() - timedelta(minutes=5)
        statement = (
            select(self.model_db)
            .where(self.model_db.factura_id.is_(None))  # type: ignore
            .where(self.model_db.q_intentos > 0)
            .where(self.model_db.fecha < datetime)
        )
        result = await session.execute(statement)
        return list(result.scalars().all()) or []


class CompraQuery(BaseQuery[Compra, CompraCreate]):
    def __init__(self) -> None:
        super().__init__(Compra, CompraCreate)

    async def get_by_provider_number(self, session: AsyncSession, provider_number: str) -> Compra | None:
        statement = select(self.model_db).where(self.model_db.numero_factura_proveedor == provider_number)
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_provider_numbers(self, session: AsyncSession, provider_numbers: list[str]) -> list[Compra]:
        statement = select(self.model_db).where(self.model_db.numero_factura_proveedor.in_(provider_numbers))  # type: ignore
        result = await session.execute(statement)
        return list(result.scalars().all())

    async def get_pendientes_facturar(self, session: AsyncSession) -> list[Compra]:
        # factura_id = '' o q_intentos > 0
        # Se restan 5 minutos para evitar obtener pedidos que se están procesando en el momento.
        datetime = DateTz.local() - timedelta(minutes=5)
        statement = (
            select(self.model_db)
            .where(self.model_db.factura_id.is_(None))  # type: ignore
            .where(self.model_db.q_intentos > 0)
            .where(self.model_db.fecha < datetime)
        )
        result = await session.execute(statement)
        return list(result.scalars().all()) or []
