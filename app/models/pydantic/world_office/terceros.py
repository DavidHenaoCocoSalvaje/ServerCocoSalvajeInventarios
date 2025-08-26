# app.models.pydantic.world_office.terceros

from app.models.pydantic.world_office.base import WOResponse
from app.models.pydantic.world_office.general import WOUbicacionDepartamento, WOCiudad
from app.models.pydantic.base import Base


class TerceroTipo(Base):
    id: int | None = None
    nombre: str | None = None
    codigo: str | None = None


class Ubicacion(Base):
    id: int | None = None
    nombre: str | None = None
    codigo: str | None = None
    ubicacionCiudad: WOCiudad | None = None
    codAlterno: str | None = None


class Ciudad(Base):
    id: int | None = None
    ciudadNombre: str | None = None
    nombre: str | None = None
    codigo: str | None = None
    senSistema: bool | None = None
    ubicacionDepartamento: WOUbicacionDepartamento | None = None


class DireccionPrincipal(Base):
    id: int | None = None
    direccion: str | None = None
    ciudad: str | None = None
    telefonoPrincipal: str | None = None
    emailPrincipal: str | None = None
    sucursal: str | None = None
    senPrincipal: bool | None = None


class TerceroTipoIdentificacion(Base):
    id: int | None = None
    abreviatura: str | None = None
    nombre: str | None = None
    codigo: str | None = None
    senEsEmpresa: bool | None = None
    senManejaDV: bool | None = None


class TerceroTipoDireccion(Base):
    id: int | None = None
    nombre: str | None = None


class TerceroZonaPOJO(Base):
    id: int | None = None
    nombre: str | None = None
    codigo: str | None = None
    senActivo: bool | None = None
    folder: bool | None = None
    borrador: bool | None = None


class Direccion(Base):
    id: int | None = None
    nombre: str | None = None
    terceroTipoDireccion: TerceroTipoDireccion | None = None
    direccion: str | None = None
    senPrincipal: bool | None = None
    ubicacionCiudad: WOCiudad | None = None
    ubicacionBarrio: Ubicacion | None = None
    indicaciones: str | None = None
    telefonoPrincipal: str | None = None
    terceroZonaPojo: TerceroZonaPOJO | None = None
    emailPrincipal: str | None = None


class WOTercero(Base):
    id: int | None = None
    terceroTipoIdentificacion: TerceroTipoIdentificacion | None = None
    identificacion: str | None = None
    digitoVerificacionGenerado: bool | None = None
    primerNombre: str | None = None
    segundoNombre: str | None = None
    primerApellido: str | None = None
    segundoApellido: str | None = None
    nombreCompleto: str | None = None
    nombreCompletoEmpleado: str | None = None
    ciudad: Ciudad | None = None
    codigo: str | None = None
    senActivo: bool | None = None
    senManejaNomina: bool | None = None
    atributos: bool | None = None
    aplicaICAVentas: bool | None = None
    terceroTipos: list[TerceroTipo] | None = None
    tieneDirPrincipal: bool | None = None
    direccionPrincipal: DireccionPrincipal | None = None


class WOTerceroResponse(WOResponse):
    data: WOTercero | None = None


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
    idTerceroTipoIdentificacion: int | None = None
    identificacion: str | None = None
    primerNombre: str | None = None
    segundoNombre: str | None = None
    primerApellido: str | None = None
    segundoApellido: str | None = None
    idCiudad: int | None = None
    codigo: str | None = None
    senActivo: bool | None = None
    idTerceroTipos: list[int] | None = None
    idTerceroTipoContribuyente: int | None = None
    idClasificacionImpuestos: int | None = None
    direccion: str | None = None
    telefono: str | None = None
    email: str | None = None
    plazoDias: int | None = None
    responsabilidadFiscal: list[int] | None = None
    direcciones: list[Direccion] | None = None
    idListaPrecioPredeterminada: int | None = None
    idTerceroVendedorPredeterminado: int | None = None
    idFormaPagoPredeterminada: int | None = None
    idLocal: int | None = None
    soloCrearDireccion: bool | None = None
