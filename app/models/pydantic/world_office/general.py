# app.models.pydantic.world_office.general

from app.models.pydantic.world_office.base import WODataList, WOResponse
from app.models.pydantic.base import Base


class WOUbicacionPais(Base):
    id: int | None = None
    nombre: str | None = None
    codigo: str | None = None
    codAlterno: str | None = None


class WOUbicacionDepartamento(Base):
    id: int | None = None
    nombre: str | None = None
    codigo: str | None = None
    senSistema: bool | None = None
    ubicacionPais: WOUbicacionPais | None = None


class WOCiudad(Base):
    id: int | None = None
    ciudadNombre: str | None = None
    nombre: str | None = None
    codigo: str | None = None
    senSistema: bool | None = None
    ubicacionDepartamento: WOUbicacionDepartamento | None = None


class WOContentCiudades(Base):
    content: list[WOCiudad] | None = None


class WODataListCiudades(WODataList):
    content: list[WOCiudad] | None = None


class WOListaCiudadesResponse(WOResponse):
    data: WOContentCiudades | None = None
