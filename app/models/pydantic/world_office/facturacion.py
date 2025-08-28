# app.models.pydantic.world_office.facturacion
from datetime import date
from pydantic import Field
from app.internal.gen.utilities import DateTz
from app.models.pydantic.base import Base
from app.models.pydantic.world_office.base import WODataList, WOResponse
from app.models.pydantic.world_office.general import WOUbicacionPais, WOCiudad
from app.models.pydantic.world_office.terceros import TerceroTipo


class WOReglone(Base):
    idInventario: int = 0
    unidadMedida: str = ''
    cantidad: int = 0
    valorUnitario: float = 0
    idBodega: int = 0
    porDescuento: float = 0
    idCentroCosto: int | None = None


class WORegloneEdit(WOReglone):
    id: int = 0


class WODocumentoVentaCreateEditBase(Base):
    fecha: date = Field(default_factory=DateTz.today)
    prefijo: int = 0
    documentoTipo: str = ''
    concepto: str = ''
    idEmpresa: int = 0
    idTerceroExterno: int = 0
    idTerceroInterno: int = 0
    idFormaPago: int = 0
    idMoneda: int = 0


class WODocumentoVentaCreate(WODocumentoVentaCreateEditBase):
    reglones: list[WOReglone] = []


class WODocumentoVentaEdit(WODocumentoVentaCreateEditBase):
    id: int = 0
    reglones: list[WORegloneEdit] = []


class WODocumentoVenta(Base):
    id: int = 0
    prefijo: str = ''
    idPrefijo: int = 0
    numero: int = 0
    fecha: date = Field(default_factory=date.today)
    empresa: str = ''
    empresaPrefijo: str = ''
    idEmpresa: int = 0
    terceroExterno: str = ''
    primerNombreTerceroExterno: str = ''
    segundoNombreTerceroExterno: str = ''
    primerApellidoTerceroExterno: str = ''
    segundoApellidoTerceroExterno: str = ''
    idTerceroExterno: int = 0
    terceroInterno: str = ''
    primerNombreTerceroInterno: str = ''
    segundoNombreTerceroInterno: str = ''
    primerApellidoTerceroInterno: str = ''
    segundoApellidoTerceroInterno: str = ''
    idTerceroInterno: int = 0
    formaPago: str = ''
    idFormaPago: int = 0
    concepto: str = ''
    responsable: str = ''
    senContabilizado: bool = False
    senCuadrado: bool = False
    senPresentadoElectronicamente: bool = False
    senAnulado: bool = False


class WOContentDocumentosVenta(WODataList):
    content: list[WODocumentoVenta] = []


class WOListaDocumentosVentaResponse(WOResponse):
    data: WOContentDocumentosVenta = WOContentDocumentosVenta()


class WOInventario(Base):
    id: int = 0
    descripcion: str = ''
    codigo: str = ''
    clasificacion: str = ''
    meses: str = ''
    senManejaLotes: bool = False
    senManejaSeriales: bool = False
    senManejaTallaColor: bool = False
    senManejaAIU: bool = False


class WOInventarioBodega(Base):
    id: int = 0
    nombre: str = ''
    senActiva: bool = False
    senPredeterminada: bool = False
    codigo: int = 0
    mapa: int = 0


class WOUnidadMedidaAdministradorImpuestos(Base):
    id: int = 0
    codigo: int = 0
    descripcion: str = ''
    ubicacionPais: WOUbicacionPais = WOUbicacionPais()


class WOUnidadMedidaTipo(Base):
    id: int = 0
    nombre: str = ''


class WOUnidadMedida(Base):
    id: int = 0
    nombre: str = ''
    codigo: str = ''
    senDeSistema: bool = False
    unidadMedidaTipo: WOUnidadMedidaTipo = WOUnidadMedidaTipo()
    unidadMedidaAdministradorImpuestos: WOUnidadMedidaAdministradorImpuestos = WOUnidadMedidaAdministradorImpuestos()
    unidadMedidaBaseId: int = 0
    factor: float = 0.0


class WOProductoDocumento(Base):
    id: int = 0
    inventario: WOInventario = WOInventario()
    inventarioBodega: WOInventarioBodega = WOInventarioBodega()
    unidadMedida: WOUnidadMedida = WOUnidadMedida()
    cantidad: int = 0
    valorUnitario: str = ''
    valorTotalRenglon: str = ''
    porcentajeDescuento: int = 0
    centroCosto: dict = {}
    tercero: dict = {}
    concepto: str = ''
    estaCruzado: bool = False
    renglonCruceId: int = 0
    senObsequio: bool = False
    precio: str = ''
    precioRenglon: str = ''
    tallaColor: str = ''
    lote: list = []
    seriales: list = []


class WOContentProductosDocumentoVenta(WODataList):
    content: list[WOProductoDocumento] = []


class WOListaProductosDocumentoVentaResponse(WOResponse):
    data: WOContentProductosDocumentoVenta = WOContentProductosDocumentoVenta()


class WOPrefijo(Base):
    id: int = 0
    nombre: str = ''
    descripcion: str = ''


class WODocumentoTipo(Base):
    id: int = 0
    codigoDocumento: str = ''
    nombreDocumento: str = ''


class WOTerceroTipoIdentificacion(Base):
    id: int = 0
    abreviatura: str = ''
    nombre: str = ''
    codigo: str = ''
    senEsEmpresa: bool = False
    senManejaDV: bool = False
    ubicacionPais: WOUbicacionPais = WOUbicacionPais()


class WOEmpresaTercero(Base):
    id: int = 0
    terceroTipoIdentificacion: WOTerceroTipoIdentificacion = WOTerceroTipoIdentificacion()
    identificacion: str = ''
    digitoVerificacion: int = 0
    digitoVerificacionGenerado: bool = False
    primerNombre: str = ''
    segundoNombre: str = ''
    primerApellido: str = ''
    segundoApellido: str = ''
    nombreCompleto: str = ''
    ciudad: WOCiudad = WOCiudad()
    codigo: str = ''
    senActivo: bool = False
    senManejaNomina: bool = False
    atributos: bool = False
    tarifaICA: int = 0
    aplicaICAVentas: bool = False
    terceroTipos: list[TerceroTipo] = []


class WOResponsabilidadFiscal(Base):
    id: int = 0
    codigo: str = ''
    significado: str = ''


class WOEmpresa(Base):
    id: int = 0
    nombre: str = ''
    prefijo: str = ''
    identificacion: str = ''
    digitoVerificacion: int = 0
    digitoVerificacionGenerado: bool = False
    senPrincipal: bool = False
    numeroEstablecimientos: int = 0
    tercero: WOEmpresaTercero = WOEmpresaTercero()
    ubicacionCiudad: WOCiudad = WOCiudad()
    infoTributariaAdicional: str = ''
    responsabilidadFiscal: list[WOResponsabilidadFiscal] = []


class WOTerceroVendedorPredeterminado(Base):
    id: int = 0
    nombreCompleto: str = ''
    primerNombre: str = ''
    segundoNombre: str = ''
    primerApellido: str = ''
    segundoApellido: str = ''
    terceroTipoIdentificacion: str = ''
    identificacion: str = ''


class WOFormaPagoPredeterminada(Base):
    id: int = 0
    codigo: str = ''
    nombre: str = ''
    senManejaCupoCredito: bool = False


class WOListaPrecioPredeterminada(Base):
    id: int = 0
    nombre: str = ''


class WOTerceroExterno(Base):
    id: int = 0
    nombreCompleto: str = ''
    primerNombre: str = ''
    segundoNombre: str = ''
    primerApellido: str = ''
    segundoApellido: str = ''
    terceroTipoIdentificacion: str = ''
    identificacion: str = ''
    terceroTipoContribuyente: str = ''
    terceroClasificacionAdministradorImpuesto: str = ''
    terceroTipos: list[TerceroTipo] = []
    senCupoCredito: bool = False
    terceroVendedorPredeterminado: WOTerceroVendedorPredeterminado = WOTerceroVendedorPredeterminado()
    formaPagoPredeterminada: WOFormaPagoPredeterminada = WOFormaPagoPredeterminada()
    listaPrecioPredeterminada: WOListaPrecioPredeterminada = WOListaPrecioPredeterminada()


class WOTerceroInterno(Base):
    id: int = 0
    nombreCompleto: str = ''
    primerNombre: str = ''
    segundoNombre: str = ''
    primerApellido: str = ''
    segundoApellido: str = ''
    terceroTipoIdentificacion: str = ''
    identificacion: str = ''


class WODireccionTerceroExterno(Base):
    id: int = 0
    direccion: str = ''
    ciudad: str = ''
    telefonoPrincipal: str = ''
    sucursal: str = ''
    senPrincipal: bool = False


class WOFormaPago(Base):
    id: int = 0
    codigo: str = ''
    nombre: str = ''
    senManejaCupoCredito: bool = False


class WOMoneda(Base):
    id: int = 0
    codigo: str = ''
    nombre: str = ''
    separadorDecimales: str = ''
    separadorMiles: str = ''
    cantidadDecimales: int = 0
    simbolo: str = ''
    tieneTRM: bool = False


class WODocumentoEncabezadosEstado(Base):
    id: int = 0
    codigo: str = ''
    nombre: str = ''


class WODocAsociado(Base):
    id: int = 0
    prefijo: WOPrefijo = WOPrefijo()
    numero: int = 0
    fecha: date = Field(default_factory=date.today)
    moneda: WOMoneda = WOMoneda()
    documentoTipo: WODocumentoTipo = WODocumentoTipo()
    trm: int = 0
    versionFe: int = 0
    cufe: str = ''


class WODocumentoMotivoGeneracion(Base):
    id: int = 0
    codigo: str = ''
    motivo: str = ''


class WODocumentoTipoNotaCredito(Base):
    id: int = 0
    codigo: str = ''
    tipoNotaCredito: str = ''
    efectoEnInventario: int = 0


class WOElaboradoPor(Base):
    id: int = 0
    nombres: str = ''


class WOHistorialPrefijoPos(Base):
    numero: int = 0
    nombrePrefijo: str = ''


class WODocumentoVentaDetail(Base):
    id: int = 0
    fecha: date = Field(default_factory=date.today)
    numero: int = 0
    prefijo: WOPrefijo = WOPrefijo()
    documentoTipo: WODocumentoTipo = WODocumentoTipo()
    empresa: WOEmpresa = WOEmpresa()
    terceroExterno: WOTerceroExterno = WOTerceroExterno()
    terceroInterno: WOTerceroInterno = WOTerceroInterno()
    direccionTerceroExterno: WODireccionTerceroExterno = WODireccionTerceroExterno()
    formaPago: WOFormaPago = WOFormaPago()
    moneda: WOMoneda = WOMoneda()
    concepto: str = ''
    trm: int = 0
    senContabilizado: bool = False
    documentoEncabezadosEstados: list[WODocumentoEncabezadosEstado] = []
    numeroExterno: str = ''
    prefijoExterno: str = ''
    docAsociado: WODocAsociado = WODocAsociado()
    documentoMotivoGeneracion: WODocumentoMotivoGeneracion = WODocumentoMotivoGeneracion()
    documentoTipoNotaCredito: WODocumentoTipoNotaCredito = WODocumentoTipoNotaCredito()
    tieneRenglones: bool = False
    senGenerado: bool = False
    elaboradoPor: WOElaboradoPor = WOElaboradoPor()
    tieneResolucionElectronica: bool = False
    atributosRequeridos: bool = False
    atributosEncabezado: bool = False
    atributosRenglones: bool = False
    historialPrefijoPos: WOHistorialPrefijoPos = WOHistorialPrefijoPos()


class WODocumentoVentaDetailResponse(WOResponse):
    data: WODocumentoVentaDetail = WODocumentoVentaDetail()

    def valid(self) -> bool:
        return self.status in ['ACCEPTED', 'CREATED']


class WOContabilizarDocumentoVentaResponse(WOResponse):
    def valid(self) -> bool:
        return self.status == 'OK' and self.userMessage == 'CONTABILIZACION_EXITOSA'
