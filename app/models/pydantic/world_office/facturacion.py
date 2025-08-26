# app.models.pydantic.world_office.facturacion
from datetime import date
from app.models.pydantic.base import Base
from app.models.pydantic.world_office.base import WODataList, WOResponse
from app.models.pydantic.world_office.general import WOUbicacionPais, WOCiudad
from app.models.pydantic.world_office.terceros import TerceroTipo


class WOReglone(Base):
    idInventario: int | None = None
    unidadMedida: str | None = None
    cantidad: int | None = None
    valorUnitario: int | None = None
    idBodega: int | None = None
    idCentroCosto: int | None = None


class WORegloneEdit(WOReglone):
    id: int | None = None


class WODocumentoVentaCreateEditBase(Base):
    fecha: date | None = None
    prefijo: int | None = None
    documentoTipo: str | None = None
    concepto: str | None = None
    idEmpresa: int | None = None
    idTerceroExterno: int | None = None
    idTerceroInterno: int | None = None
    idFormaPago: int | None = None
    idMoneda: int | None = None


class WODocumentoVentaCreate(WODocumentoVentaCreateEditBase):
    reglones: list[WOReglone] | None = None


class WODocumentoVentaEdit(WODocumentoVentaCreateEditBase):
    id: int | None = None
    reglones: list[WORegloneEdit] | None = None


class WODocumentoVenta(Base):
    id: int | None = None
    prefijo: str | None = None
    idPrefijo: int | None = None
    numero: int | None = None
    fecha: date | None = None
    empresa: str | None = None
    empresaPrefijo: str | None = None
    idEmpresa: int | None = None
    terceroExterno: str | None = None
    primerNombreTerceroExterno: str | None = None
    segundoNombreTerceroExterno: str | None = None
    primerApellidoTerceroExterno: str | None = None
    segundoApellidoTerceroExterno: str | None = None
    idTerceroExterno: int | None = None
    terceroInterno: str | None = None
    primerNombreTerceroInterno: str | None = None
    segundoNombreTerceroInterno: str | None = None
    primerApellidoTerceroInterno: str | None = None
    segundoApellidoTerceroInterno: str | None = None
    idTerceroInterno: int | None = None
    formaPago: str | None = None
    idFormaPago: int | None = None
    concepto: str | None = None
    responsable: str | None = None
    senContabilizado: bool | None = None
    senCuadrado: bool | None = None
    senPresentadoElectronicamente: bool | None = None
    senAnulado: bool | None = None


class WOContentDocumentosVenta(WODataList):
    content: list[WODocumentoVenta] | None = None


class WOListaDocumentosVentaResponse(WOResponse):
    data: WOContentDocumentosVenta | None = None


class WOInventario(Base):
    id: int | None = None
    descripcion: str | None = None
    codigo: str | None = None
    clasificacion: str | None = None
    meses: str | None = None
    senManejaLotes: bool | None = None
    senManejaSeriales: bool | None = None
    senManejaTallaColor: bool | None = None
    senManejaAIU: bool | None = None


class WOInventarioBodega(Base):
    id: int | None = None
    nombre: str | None = None
    senActiva: bool | None = None
    senPredeterminada: bool | None = None
    codigo: int | None = None
    mapa: int | None = None


class WOUnidadMedidaAdministradorImpuestos(Base):
    id: int | None = None
    codigo: int | None = None
    descripcion: str | None = None
    ubicacionPais: WOUbicacionPais | None = None


class WOUnidadMedidaTipo(Base):
    id: int | None = None
    nombre: str | None = None


class WOUnidadMedida(Base):
    id: int | None = None
    nombre: str | None = None
    codigo: str | None = None
    senDeSistema: bool | None = None
    unidadMedidaTipo: WOUnidadMedidaTipo | None = None
    unidadMedidaAdministradorImpuestos: WOUnidadMedidaAdministradorImpuestos | None = None
    unidadMedidaBaseId: int | None = None
    factor: float | None = None


class WOProductoDocumento(Base):
    id: int | None = None
    inventario: WOInventario | None = None
    inventarioBodega: WOInventarioBodega | None = None
    unidadMedida: WOUnidadMedida | None = None
    cantidad: int | None = None
    valorUnitario: str | None = None
    valorTotalRenglon: str | None = None
    porcentajeDescuento: int | None = None
    centroCosto: dict | None = None
    tercero: dict | None = None
    concepto: str | None = None
    estaCruzado: bool | None = None
    renglonCruceId: int | None = None
    senObsequio: bool | None = None
    precio: str | None = None
    precioRenglon: str | None = None
    tallaColor: str | None = None
    lote: list | None = None
    seriales: list | None = None


class WOContentProductosDocumentoVenta(WODataList):
    content: list[WOProductoDocumento] | None = None


class WOListaProductosDocumentoVentaResponse(WOResponse):
    data: WOContentProductosDocumentoVenta | None = None


class WOPrefijo(Base):
    id: int | None = None
    nombre: str | None = None
    descripcion: str | None = None


class WODocumentoTipo(Base):
    id: int | None = None
    codigoDocumento: str | None = None
    nombreDocumento: str | None = None


class WOTerceroTipoIdentificacion(Base):
    id: int | None = None
    abreviatura: str | None = None
    nombre: str | None = None
    codigo: str | None = None
    senEsEmpresa: bool | None = None
    senManejaDV: bool | None = None
    ubicacionPais: WOUbicacionPais | None = None


class WOEmpresaTercero(Base):
    id: int | None = None
    terceroTipoIdentificacion: WOTerceroTipoIdentificacion | None = None
    identificacion: str | None = None
    digitoVerificacion: int | None = None
    digitoVerificacionGenerado: bool | None = None
    primerNombre: str | None = None
    segundoNombre: str | None = None
    primerApellido: str | None = None
    segundoApellido: str | None = None
    nombreCompleto: str | None = None
    ciudad: WOCiudad | None = None
    codigo: str | None = None
    senActivo: bool | None = None
    senManejaNomina: bool | None = None
    atributos: bool | None = None
    tarifaICA: int | None = None
    aplicaICAVentas: bool | None = None
    terceroTipos: list[TerceroTipo] | None = None


class WOResponsabilidadFiscal(Base):
    id: int | None = None
    codigo: str | None = None
    significado: str | None = None


class WOEmpresa(Base):
    id: int | None = None
    nombre: str | None = None
    prefijo: str | None = None
    identificacion: str | None = None
    digitoVerificacion: int | None = None
    digitoVerificacionGenerado: bool | None = None
    senPrincipal: bool | None = None
    numeroEstablecimientos: int | None = None
    tercero: WOEmpresaTercero | None = None
    ubicacionCiudad: WOCiudad | None = None
    infoTributariaAdicional: str | None = None
    responsabilidadFiscal: list[WOResponsabilidadFiscal] | None = None


class WOTerceroVendedorPredeterminado(Base):
    id: int | None = None
    nombreCompleto: str | None = None
    primerNombre: str | None = None
    segundoNombre: str | None = None
    primerApellido: str | None = None
    segundoApellido: str | None = None
    terceroTipoIdentificacion: str | None = None
    identificacion: str | None = None


class WOFormaPagoPredeterminada(Base):
    id: int | None = None
    codigo: str | None = None
    nombre: str | None = None
    senManejaCupoCredito: bool | None = None


class WOListaPrecioPredeterminada(Base):
    id: int | None = None
    nombre: str | None = None


class WOTerceroExterno(Base):
    id: int | None = None
    nombreCompleto: str | None = None
    primerNombre: str | None = None
    segundoNombre: str | None = None
    primerApellido: str | None = None
    segundoApellido: str | None = None
    terceroTipoIdentificacion: str | None = None
    identificacion: str | None = None
    terceroTipoContribuyente: str | None = None
    terceroClasificacionAdministradorImpuesto: str | None = None
    terceroTipos: list[TerceroTipo] | None = None
    senCupoCredito: bool | None = None
    terceroVendedorPredeterminado: WOTerceroVendedorPredeterminado | None = None
    formaPagoPredeterminada: WOFormaPagoPredeterminada | None = None
    listaPrecioPredeterminada: WOListaPrecioPredeterminada | None = None


class WOTerceroInterno(Base):
    id: int | None = None
    nombreCompleto: str | None = None
    primerNombre: str | None = None
    segundoNombre: str | None = None
    primerApellido: str | None = None
    segundoApellido: str | None = None
    terceroTipoIdentificacion: str | None = None
    identificacion: str | None = None


class WODireccionTerceroExterno(Base):
    id: int | None = None
    direccion: str | None = None
    ciudad: str | None = None
    telefonoPrincipal: str | None = None
    sucursal: str | None = None
    senPrincipal: bool | None = None


class WOFormaPago(Base):
    id: int | None = None
    codigo: str | None = None
    nombre: str | None = None
    senManejaCupoCredito: bool | None = None


class WOMoneda(Base):
    id: int | None = None
    codigo: str | None = None
    nombre: str | None = None
    separadorDecimales: str | None = None
    separadorMiles: str | None = None
    cantidadDecimales: int | None = None
    simbolo: str | None = None
    tieneTRM: bool | None = None


class WODocumentoEncabezadosEstado(Base):
    id: int | None = None
    codigo: str | None = None
    nombre: str | None = None


class WODocAsociado(Base):
    id: int | None = None
    prefijo: WOPrefijo | None = None
    numero: int | None = None
    fecha: date | None = None
    moneda: WOMoneda | None = None
    documentoTipo: WODocumentoTipo | None = None
    trm: int | None = None
    versionFe: int | None = None
    cufe: str | None = None


class WODocumentoMotivoGeneracion(Base):
    id: int | None = None
    codigo: str | None = None
    motivo: str | None = None


class WODocumentoTipoNotaCredito(Base):
    id: int | None = None
    codigo: str | None = None
    tipoNotaCredito: str | None = None
    efectoEnInventario: int | None = None


class WOElaboradoPor(Base):
    id: int | None = None
    nombres: str | None = None


class WOHistorialPrefijoPos(Base):
    numero: int | None = None
    nombrePrefijo: str | None = None


class WODocumentoVentaDetail(Base):
    id: int | None = None
    fecha: date | None = None
    numero: int | None = None
    prefijo: WOPrefijo | None = None
    documentoTipo: WODocumentoTipo | None = None
    empresa: WOEmpresa | None = None
    terceroExterno: WOTerceroExterno | None = None
    terceroInterno: WOTerceroInterno | None = None
    direccionTerceroExterno: WODireccionTerceroExterno | None = None
    formaPago: WOFormaPago | None = None
    moneda: WOMoneda | None = None
    concepto: str | None = None
    trm: int | None = None
    senContabilizado: bool | None = None
    documentoEncabezadosEstados: list[WODocumentoEncabezadosEstado] | None = None
    numeroExterno: str | None = None
    prefijoExterno: str | None = None
    docAsociado: WODocAsociado | None = None
    documentoMotivoGeneracion: WODocumentoMotivoGeneracion | None = None
    documentoTipoNotaCredito: WODocumentoTipoNotaCredito | None = None
    tieneRenglones: bool | None = None
    senGenerado: bool | None = None
    elaboradoPor: WOElaboradoPor | None = None
    tieneResolucionElectronica: bool | None = None
    atributosRequeridos: bool | None = None
    atributosEncabezado: bool | None = None
    atributosRenglones: bool | None = None
    historialPrefijoPos: WOHistorialPrefijoPos | None = None


class WODocumentoVentaDetailResponse(WOResponse):
    data: WODocumentoVentaDetail | None = None
