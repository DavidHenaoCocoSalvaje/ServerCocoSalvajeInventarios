# app.models.pydantic.world_office.terceros
if __name__ == '__main__':
    from os.path import abspath
    from sys import path as sys_path

    sys_path.append(abspath('.'))


from dataclasses import dataclass
from enum import Enum
from typing import Annotated, Any
from pydantic import BeforeValidator, computed_field, PlainSerializer
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


@dataclass
class Id_Codigo:
    id: int = 0
    codigo: str = ''


class ResponsabilidadFiscal(Enum):
    GRAN_CONTRIBUYENTE = Id_Codigo(id=1, codigo='O-13')
    AUTORETENEDOR = Id_Codigo(id=2, codigo='O-15')
    AGENTE_DE_RETENCION_IVA = Id_Codigo(id=3, codigo='O-23')
    REGIMEN_SIMPLE_DE_TRIBUTACION = Id_Codigo(id=4, codigo='O-47')
    NO_APLICA = Id_Codigo(id=5, codigo='R-99-PN')
    IMPUESTO_SOBRE_LAS_VENTAS_IVA = Id_Codigo(id=6, codigo='O-48')
    NO_RESPONSABLE_DE_IVA = Id_Codigo(id=7, codigo='O-49')

    @property
    def id(self):
        return self.value.id

    @property
    def codigo(self):
        return self.value.codigo

    @classmethod
    def buscar(cls, v: Any):
        """Busca por ID (int), Código (str) o Objeto Responsabilidad"""
        # Si ya es el Enum, devolverlo
        if isinstance(v, cls):
            return v

        # Si es el objeto valor (Responsabilidad)
        if isinstance(v, Id_Codigo):
            v = v.id

        # Búsqueda por ID o Código
        for miembro in cls:
            if v == miembro.value.id or v == miembro.value.codigo:
                return miembro

        raise ValueError(f'No se encontró Responsabilidad Fiscal con valor: {v}')


ResponsabilidadFiscalField = Annotated[
    ResponsabilidadFiscal,
    BeforeValidator(ResponsabilidadFiscal.buscar),
    PlainSerializer(lambda x: x.id, return_type=int),
]


class WOTerceroCreateEdit(Base):
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
    responsabilidadFiscal: list[ResponsabilidadFiscalField]
    direcciones: list[WODireccion]
    idListaPrecioPredeterminada: int = 0
    idTerceroVendedorPredeterminado: int = 0
    idFormaPagoPredeterminada: int = 0
    idLocal: int = 0
    soloCrearDireccion: bool = False


if __name__ == '__main__':
    wo_tercero_create = WOTerceroCreateEdit(
        idTerceroTipoIdentificacion=6,
        identificacion='123456789',
        primerNombre='Juan',
        primerApellido='Perez',
        idCiudad=1,
        direccion='Calle 123',
        telefono='123456789',
        email='juan.perez@example.com',
        plazoDias=30,
        responsabilidadFiscal=[
            ResponsabilidadFiscal.IMPUESTO_SOBRE_LAS_VENTAS_IVA,
            ResponsabilidadFiscal.AUTORETENEDOR,
        ],
        direcciones=[
            WODireccion(
                nombre='Principal',
                direccion='Calle 123',
            )
        ],
        idTerceroTipos=[6],
        idTerceroTipoContribuyente=6,
        idClasificacionImpuestos=1,
        soloCrearDireccion=False,
    )
    print(wo_tercero_create.model_dump_json(indent=4))
    print(ResponsabilidadFiscal.buscar(1))
