# app.models.db.transacciones

"""_summary_
En este módulo se encuentran los modelos que representan los registros de transacciones enviadas a WorldOffie y su estado.
"""

from datetime import datetime
from enum import Enum
from sqlmodel import SQLModel, Field, TIMESTAMP, TEXT, SMALLINT

if __name__ == '__main__':
    from os.path import abspath
    from sys import path as sys_path

    sys_path.append(abspath('.'))

from app.internal.gen.utilities import DateTz


class TransaccionBase(SQLModel):
    __table_args__ = {'schema': 'transaccion'}
    fecha: datetime = Field(sa_type=TIMESTAMP(timezone=True), default_factory=DateTz.local)  # type: ignore


class PedidoLogs(Enum):
    NO_FACTURAR = 'No facturar'
    FALTA_DOCUMENTO_DE_IDENTIDAD = 'Falta documento de identidad'


class PedidoCreate(TransaccionBase):
    numero: int | None = None  # Número de pedido shopify ej. #1234
    factura_id: int | None = None  # Creación exitosa cuando se recibe número de factura
    factura_numero: int | None = None  # Creación exitosa cuando se recibe número de factura
    contabilizado: bool = False
    pago: bool = False
    log: str | PedidoLogs | None = Field(sa_type=TEXT, default=None)
    q_intentos: int = Field(
        sa_type=SMALLINT, default=3
    )  # Determina los intentos de reprocesar si el pedido no está facturado/contabilizado


class Pedido(PedidoCreate, table=True):
    __tablename__ = 'pedidos'  # type: ignore
    id: int = Field(primary_key=True, default=None)


if __name__ == '__main__':
    pedido = PedidoCreate()
    pedido.log = PedidoLogs.NO_FACTURAR.value
    print(pedido.model_dump_json(indent=2))
