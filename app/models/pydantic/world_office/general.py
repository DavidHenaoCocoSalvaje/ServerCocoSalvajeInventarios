# app.models.pydantic.world_office.general

from app.models.pydantic.world_office.base import WODataList, WOResponse
from app.models.pydantic.base import Base


class WOUbicacionPais(Base):
    id: int = 0
    nombre: str = ''
    codigo: str = ''
    codAlterno: str = ''


class WOUbicacionDepartamento(Base):
    id: int = 0
    nombre: str = ''
    codigo: str = ''
    senSistema: bool = False
    ubicacionPais: WOUbicacionPais = WOUbicacionPais()


class WOCiudad(Base):
    id: int = 0
    ciudadNombre: str = ''
    nombre: str = ''
    codigo: str = ''
    senSistema: bool = False
    ubicacionDepartamento: WOUbicacionDepartamento = WOUbicacionDepartamento()


class WOContentCiudades(Base):
    content: list[WOCiudad] = []


class WODataListCiudades(WODataList):
    content: list[WOCiudad] = []


class WOListaCiudadesResponse(WOResponse):
    data: WOContentCiudades = WOContentCiudades()

    def valid(self) -> bool:
        return self.status == 'OK'
