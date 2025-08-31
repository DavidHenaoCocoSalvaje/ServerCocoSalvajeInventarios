# app.models.db.transacciones

"""_summary_
En este módulo se encuentran los modelos que representan los registros de transacciones enviadas a WorldOffie y su estado.
"""

from datetime import datetime
from sqlmodel import SQLModel, Field, TIMESTAMP, TEXT

from app.internal.gen.utilities import DateTz


class TransaccionBase(SQLModel):
    __table_args__ = {'schema': 'transaccion'}
    fecha: datetime = Field(sa_type=TIMESTAMP(timezone=True), default_factory=DateTz.local)  # type: ignore


class PedidoCreate(TransaccionBase):
    numero: str = ''  # Número de pedido shopify ej. #1234
    factura_id: str = ''  # Creación exitosa cuando se recibe número de factura
    factura_numero: str = ''  # Creación exitosa cuando se recibe número de factura
    contabilizado: bool = False
    log: str = Field(sa_type=TEXT, default='')


class Pedido(PedidoCreate, table=True):
    __tablename__ = 'pedidos'  # type: ignore
    id: int | None = Field(primary_key=True, default=None)
