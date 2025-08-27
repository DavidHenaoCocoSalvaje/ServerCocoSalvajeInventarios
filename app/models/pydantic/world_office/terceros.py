# app.models.pydantic.world_office.terceros

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


class Direccion(Base):
    id: int = 0
    nombre: str = ''
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

    @computed_field
    @property
    def idTerceroTipos(self) -> list[int]:
        return list(map(lambda x: x.id, self.terceroTipos))


class WOTerceroResponse(WOResponse):
    data: WOTercero = WOTercero()

    def valid(self) -> bool:
        # Se asume NOT_FOUND found como valido ya que no representa un error.
        return self.status in ['OK', 'NOT_FOUND', 'CREATED']


class WOTerceroCreate(Base):
    """Crea un tercero en World Office, se listan las propiedades requeridas.
    Args:
        idTerceroTipoIdentificacion (int): ID del tipo de identificación.
        identificacion (str): Número de identificación.
        primerNombre (str): Primer nombre.
        primerApellido (str): Primer apellido.
        idCiudad (int): ID de la ciudad.
        idTerceroTipos (list[int]): IDs de los tipos de tercero.
        idTerceroTipoContribuyente (int): ID del tipo de contribuyente.
        idClasificacionImpuestos (int): ID de la clasificación de impuestos.
        direccion (str): Dirección.
        telefono (str): Teléfono.
        email (str): Email.
        plazoDias (int): Plazo en días.
        responsabilidadFiscal (list[int]): IDs de las responsabilidades fiscales.
    """

    id: int | None = None
    idTerceroTipoIdentificacion: int = 0
    identificacion: str = ''
    primerNombre: str = ''
    segundoNombre: str = ''
    primerApellido: str = ''
    segundoApellido: str = ''
    idCiudad: int = 0
    codigo: str = ''
    senActivo: bool = False
    idTerceroTipos: list[int] = []
    idTerceroTipoContribuyente: int = 0
    idClasificacionImpuestos: int = 0
    direccion: str = ''
    telefono: str = ''
    email: str = ''
    plazoDias: int = 0
    responsabilidadFiscal: list[int] = []
    direcciones: list[Direccion] = []
    idListaPrecioPredeterminada: int = 0
    idTerceroVendedorPredeterminado: int = 0
    idFormaPagoPredeterminada: int = 0
    idLocal: int = 0
    soloCrearDireccion: bool = False
