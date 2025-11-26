# app.models.pydantic.world_office.inventario

from typing import Annotated

from pydantic import BeforeValidator
from app.models.pydantic.base import Base
from app.models.pydantic.world_office.base import WOResponse


class Contabilizacion(Base):
    id: int = 0
    nombre: str = ''
    codigo: str = ''
    senDeSistema: bool = False
    codAlterno: str = ''
    senAfectaCostoPromedio: bool = False


class Empresa(Base):
    id: int = 0
    nombre: str = ''
    prefijo: str = ''
    identificacion: str = ''
    digitoVerificacion: int = 0
    digitoVerificacionGenerado: bool = False
    senPrincipal: bool = False
    numeroEstablecimientos: int = 0
    tercero: dict = {}
    ubicacionCiudad: dict = {}
    infoTributariaAdicional: str = ''
    responsabilidadFiscal: list = []
    tieneLogo: bool = False


class Impuesto(Base):
    id: int = 0
    tipo: str = ''
    nombre: str = ''
    tipoCobro: str = ''
    tarifa: int = 0
    empresas: list = []


class InventarioTipoImpuestoVenta(Base):
    id: int = 0
    nombre: str = ''
    tipo: str = ''
    ubicacionPais: Contabilizacion = Contabilizacion()


class ImpuestoElement(Base):
    id: int = 0
    valor: float = 0
    senSumaAlCosto: bool = False
    idProceso: int = 0
    impuesto: Impuesto = Impuesto()
    empresas: list[Empresa] = []
    inventarioTipoImpuestoVenta: InventarioTipoImpuestoVenta = InventarioTipoImpuestoVenta()
    muestraAlerta: bool = False


class UnidadMedida(Base):
    id: int = 0
    nombre: str = ''
    codigo: str = ''
    senDeSistema: bool = False
    unidadMedidaTipo: dict = {}
    unidadMedidaAdministradorImpuestos: dict = {}
    unidadMedidaBaseId: int = 0
    factor: int = 0


class Grupo(Base):
    id: int = 0
    codigo: str = ''
    nombreGrupo: str = ''
    folder: bool = False
    seleccionado: bool = False
    senActivo: bool = False
    padre: str = ''
    cantidadHijos: int = 0
    borrador: bool = False


class WOInventario(Base):
    id: Annotated[str, BeforeValidator(lambda x: str(x))] = ''
    codigo: str = ''
    codigoInternacional: str = ''
    descripcion: str = ''
    unidadMedida: UnidadMedida = UnidadMedida()
    senActivo: bool = False
    inventarioClasificacion: Contabilizacion = Contabilizacion()
    centroCosto: dict = {}
    contabilizacion: Contabilizacion = Contabilizacion()
    senFacturarSinExistencias: bool = False
    senManejaSeriales: bool = False
    perteneceAUnProducto: bool = False
    utilidadEstimada: int = 0
    impuestos: list[ImpuestoElement] = []
    atributos: bool = False
    senManejaLotes: bool = False
    senFavorito: bool = False
    senNoModificable: bool = False
    senManejaTallaColor: bool = False
    senVerEnPos: bool = False
    fechaInicioTallaColor: str = ''
    fechaInicioSeriales: str = ''
    fechaInicioLotes: str = ''
    grupo: list[Grupo] = []
    fechaInicioPerteneceAUnProducto: str = ''


class WOInventarioResponse(WOResponse):
    data: WOInventario = WOInventario()

    def valid(self) -> bool:
        return self.status == 'ACCEPTED' and bool(self.data)
