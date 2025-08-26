# app.internal.integrations.world_office
if __name__ == '__main__':
    from os.path import abspath
    from sys import path as sys_path

    sys_path.append(abspath('.'))

# from random import randint


from app.internal.log import factory_logger
from app.models.pydantic.world_office.base import TipoDatoWoFiltro, TipoFiltroWoFiltro, WOFiltro, WOListar, WOResponse
from app.models.pydantic.world_office.facturacion import (
    WODocumentoVenta,
    WODocumentoVentaCreate,
    WODocumentoVentaDetail,
    WODocumentoVentaDetailResponse,
    WODocumentoVentaEdit,
    WOListaDocumentosVentaResponse,
    WOListaProductosDocumentoVentaResponse,
    WOProductoDocumento,
)
from app.models.pydantic.world_office.general import WOCiudad, WOListaCiudadesResponse
from app.models.pydantic.world_office.terceros import WOTercero, WOTerceroResponse, WOTerceroCreate
from app.internal.integrations.base import BaseClient
from app.config import config

wo_log = factory_logger('world_office', file=True)


class WoClient(BaseClient):
    class Paths:
        class Terceros:
            root: str = '/terceros'
            identificacion: str = f'{root}/identificacion'
            crear: str = f'{root}/crearTercero'

        class Ventas:
            root: str = '/documentos'
            crear: str = f'{root}/crearDocumentoVenta'
            editar: str = f'{root}/editarDocumentoVenta'
            documento_venta: str = f'{root}/getDocumentoId'
            listar_documentos_venta: str = f'{root}/listarDocumentoVenta'
            listar_productos = f'{root}/getRenglonesByDocumentoEncabezado'
            contabilizar = f'{root}/contabilizarDocumento'

        class Ciudad:
            root: str = '/ciudad'
            listar_ciudades: str = f'{root}/listarCiudades'

    def __init__(self, host: str = 'https://api.worldoffice.cloud/api'):
        super().__init__(f'{host}/{config.wo_api_version}')
        self.set_header('Content-Type', 'application/json')
        self.set_header('Authorization', f'WO {config.wo_api_key}')

    async def get_tercero(self, identificacion: str) -> WOTercero:
        tercero_json = await self.get(self.Paths.Terceros.identificacion, [identificacion])
        tercero_response = WOTerceroResponse(**tercero_json)
        if not tercero_response.data:
            raise Exception(f'No se encontró el tercero {identificacion}, response:{tercero_json}')
        return tercero_response.data

    async def get_documento_venta(self, id_documento: int) -> WODocumentoVentaDetail:
        documento_venta_json = await self.get(self.Paths.Ventas.documento_venta, [str(id_documento)])
        documento_venta_response = WODocumentoVentaDetailResponse(**documento_venta_json)
        if not documento_venta_response.data:
            raise Exception(f'No se encontró el documento {id_documento}, response:{documento_venta_json}')
        return documento_venta_response.data

    async def contabilizar_documento_venta(self, id_documento: int) -> WOResponse:
        contabilizar_json = await self.post(self.Paths.Ventas.contabilizar, [str(id_documento)])
        contabilizar_response = WOResponse(**contabilizar_json)
        return contabilizar_response

    async def crear_tercero(self, wo_tercero_create: WOTerceroCreate) -> WOTercero:
        tercero_json = await self.post(
            self.Paths.Terceros.crear, payload=wo_tercero_create.model_dump(exclude_none=True)
        )
        tercero_response = WOTerceroResponse(**tercero_json)
        if not tercero_response.data:
            raise Exception(f'WO: No se creó el tercero: {wo_tercero_create.model_dump(exclude_none=True)}')
        return tercero_response.data

    async def buscar_ciudad(self, nombre: str) -> WOCiudad:
        filtro = WOFiltro(
            atributo='nombre',
            valor=nombre,
            tipoFiltro=TipoFiltroWoFiltro.CONTIENE,
            tipoDato=TipoDatoWoFiltro.STRING,
            operador='AND',
        )
        payload = WOListar(columnaOrdenar='id', registrosPorPagina=10, orden='ASC', filtros=[filtro])
        ciudades_json = await self.post(
            self.Paths.Ciudad.listar_ciudades, payload=payload.model_dump(exclude_none=True)
        )
        ciudades_response = WOListaCiudadesResponse(**ciudades_json)
        if not ciudades_response.data.content or len(ciudades_response.data.content) == 0:
            wo_log.error(f'No se encontró la ciudad {nombre}')
            raise Exception(f'WO: No se encontró la ciudad {nombre}')
        ciudad = ciudades_response.data.content[0]
        return ciudad

    async def buscar_documento_venta(self, id_factura: int, codigo_documento: str = 'FV') -> WODocumentoVenta:
        # Filtro1 Obligatorio de acuerdo a la documentación de World Office
        filtro1 = WOFiltro(
            atributo='documentoTipo.codigoDocumento',
            valor=codigo_documento,
            tipoFiltro=TipoFiltroWoFiltro.IGUAL,
            tipoDato=TipoDatoWoFiltro.STRING,
            operador='AND',
        )
        filtro2 = WOFiltro(
            atributo='id',
            valor=id_factura,
            tipoFiltro=TipoFiltroWoFiltro.IGUAL,
            tipoDato=TipoDatoWoFiltro.NUMERIC,
            operador='AND',
        )
        payload = WOListar(
            columnaOrdenar='id', registrosPorPagina=10, orden='ASC', filtros=[filtro1, filtro2]
        ).model_dump(exclude_none=True)
        facturas_json = await self.post(self.Paths.Ventas.listar_documentos_venta, payload=payload)
        facturas_response = WOListaDocumentosVentaResponse(**facturas_json)
        if not facturas_response.data.content or len(facturas_response.data.content) == 0:
            raise Exception(f'No se encontró la factura {id_factura}')
        return facturas_response.data.content[0]

    async def productos_documento_venta(self, id_documento: int) -> list[WOProductoDocumento]:
        payload = WOListar(columnaOrdenar='id', registrosPorPagina=10, orden='ASC', filtros=[]).model_dump(
            exclude_none=True
        )
        productos_json = await self.post(
            self.Paths.Ventas.listar_productos,
            params=[str(id_documento)],
            payload=payload,
        )
        productos_response = WOListaProductosDocumentoVentaResponse(**productos_json)
        if not productos_response.data.content or len(productos_response.data.content) == 0:
            raise Exception(f'No se encontrarón los productos del documento {id_documento}')
        return productos_response.data.content

    async def crear_factura_venta(self, factura_create: WODocumentoVentaCreate) -> WODocumentoVentaDetail:
        payload = factura_create.model_dump(exclude_none=True)
        factura_json = await self.post(self.Paths.Ventas.crear, payload=payload)
        factura_response = WODocumentoVentaDetailResponse(**factura_json)
        if not factura_response.data:
            raise Exception(f'No se creó la factura payload:{payload}, response:{factura_json}')
        return factura_response.data

    async def editar_factura_venta(self, factura_edit: WODocumentoVentaEdit) -> WODocumentoVentaDetail:
        payload = factura_edit.model_dump(exclude_none=True)
        factura_json = await self.post(self.Paths.Ventas.editar, payload=payload)
        factura_response = WODocumentoVentaDetailResponse(**factura_json)
        if not factura_response.data:
            raise Exception(f'No se creó la factura payload:{payload}, response:{factura_json}')
        return factura_response.data


if __name__ == '__main__':
    from asyncio import run
    # from random import randint

    async def main():
        wo_client = WoClient()
        tercero = await wo_client.get_tercero('1094240554')
        assert tercero.identificacion == '1094240554'
        ciudad = await wo_client.buscar_ciudad('Bogotá')
        assert isinstance(ciudad, WOCiudad)
        assert ciudad.ciudadNombre and 'Bogotá' in ciudad.ciudadNombre
        factura = await wo_client.buscar_documento_venta(id_factura=31735)
        assert factura.id == 31735
        factura_detail = await wo_client.get_documento_venta(id_documento=31735)
        assert factura_detail.id == 31735
        productos_factura = await wo_client.productos_documento_venta(id_documento=31735)
        assert isinstance(productos_factura[0], WOProductoDocumento)

    run(main())
