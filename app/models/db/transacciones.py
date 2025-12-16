# app.models.db.transacciones

"""_summary_
En este módulo se encuentran los modelos que representan los registros de transacciones enviadas a WorldOffie y su estado.
"""

from pydantic.config import ConfigDict
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
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)  # type: ignore

    fecha: datetime = Field(sa_type=TIMESTAMP(timezone=True), default_factory=DateTz.local)  # type: ignore
    factura_id: int | None = None  # Creación exitosa cuando se recibe número de factura
    factura_numero: int | None = None  # Creación exitosa cuando se recibe número de factura
    contabilizado: bool = False
    q_intentos: int = Field(
        sa_type=SMALLINT, default=3
    )  # Determina los intentos de reprocesar si la transacción no está facturada/contabilizada


class PedidoLogs(Enum):
    NO_FACTURAR = 'No facturar'
    FALTA_DOCUMENTO_DE_IDENTIDAD = 'Falta documento de identidad'


class PedidoCreate(TransaccionBase):
    numero: int | None = None  # Número de pedido shopify ej. #1234
    pago: bool = False
    log: str | PedidoLogs | None = Field(sa_type=TEXT, default=None)


class Pedido(PedidoCreate, table=True):
    __tablename__ = 'pedidos'  # type: ignore
    id: int | None = Field(primary_key=True, default=None)


class CompraCreate(TransaccionBase):
    numero_factura_proveedor: str | None = None  # Número de factura proveedor ej. #FV1234
    log: str | None = Field(sa_type=TEXT, default=None)


class Compra(CompraCreate, table=True):
    __tablename__ = 'compras'  # type: ignore
    id: int = Field(primary_key=True, default=None)


if __name__ == '__main__':
    pedido = PedidoCreate()
    print(pedido.log)
    print(pedido.model_dump_json(indent=2))
