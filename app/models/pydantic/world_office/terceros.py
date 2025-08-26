# app.models.pydantic.world_office.terceros

from app.models.pydantic.world_office.base import WOResponse
from app.models.pydantic.world_office.general import WOUbicacionDepartamento, WOCiudad
from app.models.pydantic.base import Base


class TerceroTipo(Base):
    id: int | None = 0
    nombre: str | None = ''
    codigo: str | None = ''


class Ubicacion(Base):
    id: int | None = 0
    nombre: str | None = ''
    codigo: str | None = ''
    ubicacionCiudad: WOCiudad | None = WOCiudad()
    codAlterno: str | None = None


class Ciudad(Base):
    id: int | None = 0
    ciudadNombre: str | None = ''
    nombre: str | None = ''
    codigo: str | None = ''
    senSistema: bool | None = False
    ubicacionDepartamento: WOUbicacionDepartamento | None = WOUbicacionDepartamento()


class DireccionPrincipal(Base):
    id: int | None = 0
    direccion: str | None = ''
    ciudad: str | None = ''
    telefonoPrincipal: str | None = ''
    emailPrincipal: str | None = ''
    sucursal: str | None = ''
    senPrincipal: bool | None = False


class TerceroTipoIdentificacion(Base):
    id: int | None = 0
    abreviatura: str | None = ''
    nombre: str | None = ''
    codigo: str | None = ''
    senEsEmpresa: bool | None = False
    senManejaDV: bool | None = False


class TerceroTipoDireccion(Base):
    id: int | None = 0
    nombre: str | None = ''


class TerceroZonaPOJO(Base):
    id: int | None = 0
    nombre: str | None = ''
    codigo: str | None = ''
    senActivo: bool | None = False
    folder: bool | None = False
    borrador: bool | None = False


class Direccion(Base):
    id: int | None = 0
    nombre: str | None = ''
    terceroTipoDireccion: TerceroTipoDireccion | None = TerceroTipoDireccion()
    direccion: str | None = ''
    senPrincipal: bool | None = False
    ubicacionCiudad: WOCiudad | None = WOCiudad()
    ubicacionBarrio: Ubicacion | None = Ubicacion()
    indicaciones: str | None = ''
    telefonoPrincipal: str | None = ''
    terceroZonaPojo: TerceroZonaPOJO | None = TerceroZonaPOJO()
    emailPrincipal: str | None = ''


class Tercero(Base):
    id: int | None = 0
    terceroTipoIdentificacion: TerceroTipoIdentificacion | None = TerceroTipoIdentificacion()
    identificacion: str | None = ''
    digitoVerificacionGenerado: bool | None = False
    primerNombre: str | None = ''
    segundoNombre: str | None = ''
    primerApellido: str | None = ''
    segundoApellido: str | None = ''
    nombreCompleto: str | None = ''
    nombreCompletoEmpleado: str | None = ''
    ciudad: Ciudad | None = Ciudad()
    codigo: str | None = ''
    senActivo: bool | None = False
    senManejaNomina: bool | None = False
    atributos: bool | None = False
    aplicaICAVentas: bool | None = False
    terceroTipos: list[TerceroTipo] | None = []
    tieneDirPrincipal: bool | None = False
    direccionPrincipal: DireccionPrincipal | None = DireccionPrincipal()


class WOTerceroResponse(WOResponse):
    data: Tercero | None = Tercero()


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
    idTerceroTipoIdentificacion: int | None = 0
    identificacion: str | None = ''
    primerNombre: str | None = ''
    segundoNombre: str | None = ''
    primerApellido: str | None = ''
    segundoApellido: str | None = ''
    idCiudad: int | None = 0
    codigo: str | None = ''
    senActivo: bool | None = False
    idTerceroTipos: list[int] | None = []
    idTerceroTipoContribuyente: int | None = 0
    idClasificacionImpuestos: int | None = 0
    direccion: str | None = ''
    telefono: str | None = ''
    email: str | None = ''
    plazoDias: int | None = 0
    responsabilidadFiscal: list[int] | None = []
    direcciones: list[Direccion] | None = []
    idListaPrecioPredeterminada: int | None = 0
    idTerceroVendedorPredeterminado: int | None = 0
    idFormaPagoPredeterminada: int | None = 0
    idLocal: int | None = 0
    soloCrearDireccion: bool | None = False
