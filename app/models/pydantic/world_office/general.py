# app.models.pydantic.world_office.general

from app.models.pydantic.world_office.base import WODataList, WOResponse
from app.models.pydantic.base import Base


class WOUbicacionPais(Base):
    id: int | None = 0
    nombre: str | None = ''
    codigo: str | None = ''
    codAlterno: str | None = ''


class WOUbicacionDepartamento(Base):
    id: int | None = 0
    nombre: str | None = ''
    codigo: str | None = ''
    senSistema: bool | None = False
    ubicacionPais: WOUbicacionPais | None = WOUbicacionPais()


class WOCiudad(Base):
    id: int | None = 0
    ciudadNombre: str | None = ''
    nombre: str | None = ''
    codigo: str | None = ''
    senSistema: bool | None = False
    ubicacionDepartamento: WOUbicacionDepartamento | None = WOUbicacionDepartamento()


class WOContentCiudades(Base):
    content: list[WOCiudad] | None = []


class WODataListCiudades(WODataList):
    content: list[WOCiudad] | None = []


class WOListaCiudadesResponse(WOResponse):
    data: WOContentCiudades | None = WOContentCiudades()
