# app.models.pydantic.world_office.facturacion
from datetime import datetime
from app.models.pydantic.base import Base
from pydantic import Field


class Reglone(Base):
    idInventario: int | None = 0
    unidadMedida: str | None = ''
    cantidad: int | None = 0
    valorUnitario: int | None = 0
    idBodega: int | None = 0
    idCentroCosto: int | None = 0


class FacturaCreate(Base):
    fecha: datetime | None = None
    prefijo: int | None = 0
    documentoTipo: str | None = ''
    concepto: str | None = ''
    idEmpresa: int | None = 0
    idTerceroExterno: int | None = 0
    idTerceroInterno: int | None = 0
    idFormaPago: int | None = 0
    idMoneda: int | None = 0
    reglones: list[Reglone] | None = Field(default_factory=list)
