# app.models.pydantic.world_office.terceros

from enum import Enum
from pydantic import computed_field
from app.models.pydantic.world_office.base import WOResponse
from app.models.pydantic.world_office.general import WOUbicacionDepartamento, WOCiudad
from app.models.pydantic.base import Base


class TerceroTipo(Base):
    id: int = 0
    nombre: str = ''
    codigo: str = ''


class Ubicacion(Base):
    id: int = 0
    nombre: str = ''
    codigo: str = ''
    ubicacionCiudad: WOCiudad = WOCiudad()
    codAlterno: str = ''


class Ciudad(Base):
    id: int = 0
    ciudadNombre: str = ''
    nombre: str = ''
    codigo: str = ''
    senSistema: bool = False
    ubicacionDepartamento: WOUbicacionDepartamento = WOUbicacionDepartamento()


class DireccionPrincipal(Base):
    id: int = 0
    direccion: str = ''
    ciudad: str = ''
    telefonoPrincipal: str = ''
    emailPrincipal: str = ''
    sucursal: str = ''
    senPrincipal: bool = False


class TerceroTipoIdentificacion(Base):
    id: int = 0
    abreviatura: str = ''
    nombre: str = ''
    codigo: str = ''
    senEsEmpresa: bool = False
    senManejaDV: bool = False


class TerceroTipoDireccion(Base):
    id: int = 0
    nombre: str = ''


class TerceroZonaPOJO(Base):
    id: int = 0
    nombre: str = ''
    codigo: str = ''
    senActivo: bool = False
    folder: bool = False
    borrador: bool = False


class WODireccion(Base):
    id: int = 0
    nombre: str
    terceroTipoDireccion: TerceroTipoDireccion = TerceroTipoDireccion()
    direccion: str = ''
    senPrincipal: bool = False
    ubicacionCiudad: WOCiudad = WOCiudad()
    ubicacionBarrio: Ubicacion = Ubicacion()
    indicaciones: str = ''
    telefonoPrincipal: str = ''
    terceroZonaPojo: TerceroZonaPOJO = TerceroZonaPOJO()
    emailPrincipal: str = ''


class WOTercero(Base):
    id: int = 0
    terceroTipoIdentificacion: TerceroTipoIdentificacion = TerceroTipoIdentificacion()
    identificacion: str = ''
    digitoVerificacionGenerado: bool = False
    primerNombre: str = ''
    segundoNombre: str = ''
    primerApellido: str = ''
    segundoApellido: str = ''
    nombreCompleto: str = ''
    nombreCompletoEmpleado: str = ''
    ciudad: Ciudad = Ciudad()
    codigo: str = ''
    senActivo: bool = False
    senManejaNomina: bool = False
    atributos: bool = False
    aplicaICAVentas: bool = False
    terceroTipos: list[TerceroTipo] = []
    tieneDirPrincipal: bool = False
    direccionPrincipal: DireccionPrincipal = DireccionPrincipal()

    def is_client(self):
        # Verificar que alguno de los tipos sea 4
        return any(x.id == 4 for x in self.terceroTipos)

    def is_provider(self):
        # Verificar que alguno de los tipos sea 6
        return any(x.id == 6 for x in self.terceroTipos)

    @computed_field
    @property
    def idTerceroTipos(self) -> list[int]:
        return list(map(lambda x: x.id, self.terceroTipos))


class WOTerceroResponse(WOResponse):
    data: WOTercero = WOTercero()

    def valid(self) -> bool:
        # Se asume NOT_FOUND found como valido ya que no representa un error.
        return self.status in ['OK', 'NOT_FOUND', 'CREATED']


#       {
    #     "id": 1,
    #     "codigo": "O-13",
    #     "significado": "Gran Contribuyente"
    #   },
    #   {
    #     "id": 2,
    #     "codigo": "O-15",
    #     "significado": "Autorretenedor"
    #   },
    #   {
    #     "id": 3,
    #     "codigo": "O-23",
    #     "significado": "Agente de Retención IVA"
    #   },
    #   {
    #     "id": 4,
    #     "codigo": "O-47",
    #     "significado": "Régimen Simple de Tributación"
    #   },
    #   {
    #     "id": 5,
    #     "codigo": "R-99-PN",
    #     "significado": "No Aplica"
    #   },
    #   {
    #     "id": 6,
    #     "codigo": "O-48",
    #     "significado": "Impuesto Sobre las Ventas – IVA"
    #   },
    #   {
    #     "id": 7,
    #     "codigo": "O-49",
    #     "significado": "No Responsable de IVA"
    #   }
ResponsabilidadesFiscales = {
    (1, "O-13"): "GRAN_COTRIBUYENTE",
    (2, ""): ""
}

class WOTerceroCreate(Base):
    id: int | None = None
    idTerceroTipoIdentificacion: int
    identificacion: str
    primerNombre: str
    segundoNombre: str = ''
    primerApellido: str = ''
    segundoApellido: str = ''
    idCiudad: int
    codigo: str = ''
    senActivo: bool = False
    idTerceroTipos: list[int]
    idTerceroTipoContribuyente: int
    idClasificacionImpuestos: int
    direccion: str
    telefono: str
    email: str
    plazoDias: int
    responsabilidadFiscal: list[int]
    direcciones: list[WODireccion]
    idListaPrecioPredeterminada: int = 0
    idTerceroVendedorPredeterminado: int = 0
    idFormaPagoPredeterminada: int = 0
    idLocal: int = 0
    soloCrearDireccion: bool = False
