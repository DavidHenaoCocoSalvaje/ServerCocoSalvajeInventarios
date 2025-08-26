# app.models.db.transacciones

"""_summary_
En este módulo se encuentran los modelos que representan los registros de transacciones enviadas a WorldOffie y su estado.
"""

from datetime import datetime
from sqlmodel import SQLModel, Field
from enum import Enum

from app.internal.gen.utilities import DateTz


class Accion(Enum):
    CREAR = 'crear'
    MODIFICAR = 'modificar'
    ELIMINAR = 'eliminar'


class TransaccionBase(SQLModel):
    __table_args__ = {'schema': 'transaccion'}
    fecha: datetime = Field(sa_type=datetime, default_factory=DateTz.local)
    log: str = Field(default='')  # Se guarda si ocurre algún error
    payload: str = Field(
        default=''
    )  # Se guarda el payload enviado a worldoffice si no se logra procesar la transacción.


class PedidoCreate(TransaccionBase):
    acccion: Accion
    numero: str  # Número de pedido shopify ej. #1234
    factura: str = Field(default='')  # Creación exitosa cuando se recibe número de factura
    contabilizado: bool = Field(default=False)


class Pedido(PedidoCreate, table=True):
    __tablename__ = 'pedidos'  # type: ignore
    id: int | None = Field(primary_key=True, default=None)


class CustomerCreate(TransaccionBase, table=True):
    __tablename__ = 'customers'  # type: ignore
    acccion: Accion
    shopify_id: int
    wo_id: int


class Customer(CustomerCreate, table=True):
    __tablename__ = 'customers'  # type: ignore
    id: int | None = Field(primary_key=True, default=None)
