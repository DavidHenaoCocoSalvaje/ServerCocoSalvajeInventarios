# app.models.db.transacciones

"""_summary_
En este módulo se encuentran los modelos que representan los registros de transacciones enviadas a WorldOffie y su estado.
"""

from datetime import datetime
from sqlmodel import SQLModel, Field
from enum import Enum

from app.internal.gen.utilities import DateTz


class Transaccion(Enum):
    CREAR = 'crear'
    MODIFICAR = 'modificar'
    ELIMINAR = 'eliminar'


class TransaccionBase(SQLModel):
    __table_args__ = {'schema': 'transaccion'}
    id: int | None = Field(primary_key=True, default=None)
    fecha: datetime = Field(sa_type=datetime, default_factory=DateTz.local)


class Pedido(TransaccionBase, table=True):
    __tablename__ = 'transacciones'  # type: ignore
    acccion: Transaccion
    numero: str  # Número de pedido shopify ej. #1234
    factura: str = Field(default='')  # Creación exitosa cuando se recibe número de factura
    contabilizado: bool = Field(default=False)
    log: str = Field(default='')
