# app.internal.integrations.world_office
if __name__ == '__main__':
    from os.path import abspath
    from sys import path as sys_path

    sys_path.append(abspath('.'))

# from random import randint


from pydantic import ValidationError
from app.internal.log import factory_logger
from app.models.pydantic.world_office.base import TipoDatoWoFiltro, TipoFiltroWoFiltro, WOFiltro, WOListar
from app.models.pydantic.world_office.facturacion import (
    WOContabilizarDocumentoVentaResponse,
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
from app.models.pydantic.world_office.invenvario import WOInventario, WOInventarioResponse
from app.models.pydantic.world_office.terceros import WOTercero, WOTerceroResponse, WOTerceroCreate
from app.internal.integrations.base import BaseClient, ClientException
from app.config import config

wo_log = factory_logger('world_office', file=True)


class WOException(ClientException):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class WoClient(BaseClient):
    __instance = None

    class Paths:
        class Terceros:
            root: str = '/terceros'
            identificacion: str = f'{root}/identificacion'
            crear: str = f'{root}/crearTercero'
            editar: str = f'{root}/editarTercero'

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

        class Inventario:
            root: str = '/inventarios'
            inventario_por_codigo: str = f'{root}/consultaCodigo'

    # Singleton para implementar posteriormente la restricción de peticiones.
    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(WoClient, cls).__new__(cls)
        return cls.__instance

    def __init__(self, host: str = f'https://api.worldoffice.cloud/api/{config.wo_api_version}'):
        super().__init__()
        self.host = host
        self.set_header('Content-Type', 'application/json')
        self.set_header('Authorization', f'WO {config.wo_api_key}')

    async def get_tercero(self, identificacion: str) -> WOTercero | None:
        if not identificacion:
            exception = WOException(url=self.url, msg='Falta documento de identidad')
            wo_log.error(f'{exception}')
            raise exception

        tercero_json = await self.get(self.Paths.Terceros.identificacion, [identificacion])

        try:
            tercero_response = WOTerceroResponse(**tercero_json)
        except ValidationError as e:
            exception = WOException(url=self.url, response=tercero_json, msg=str(e))
            wo_log.error(f'Error al obtener tercero: {exception}')
            raise exception

        if tercero_response.valid():
            if not tercero_response.data.id:
                return None
        else:
            exception = WOException(url=self.url, response=tercero_json)
            wo_log.error(f'No se pudo obtener tercero: {exception}')
            raise exception

        return tercero_response.data

    async def get_documento_venta(self, id_documento: int) -> WODocumentoVentaDetail:
        documento_venta_json = await self.get(self.Paths.Ventas.documento_venta, [str(id_documento)])

        try:
            documento_venta_response = WODocumentoVentaDetailResponse(**documento_venta_json)
        except ValidationError as e:
            exception = WOException(url=self.url, response=documento_venta_json, msg=str(e))
            wo_log.error(f'Error al obtener documento de venta: {exception}')
            raise exception

        if not documento_venta_response.data:
            exception = WOException(url=self.url, response=documento_venta_json)
            wo_log.error(f'No se pudo obtener documento de venta: {exception}')
            raise exception
        return documento_venta_response.data

    async def get_inventario_por_codigo(self, codigo: str) -> WOInventario:
        inventario_json = await self.get(self.Paths.Inventario.inventario_por_codigo, [codigo])

        try:
            inventario_response = WOInventarioResponse(**inventario_json)
        except ValidationError as e:
            exception = WOException(url=self.url, response=inventario_json, msg=str(e))
            wo_log.error(f'Error al obtener inventario: {exception}')
            raise exception

        if not inventario_response.valid():
            exception = WOException(url=self.url, response=inventario_json)
            wo_log.error(f'No se pudo obtener inventario: {exception}')
            raise exception
        return inventario_response.data

    async def contabilizar_documento_venta(self, id_documento: int) -> bool:
        contabilizar_json = await self.post(self.Paths.Ventas.contabilizar, [str(id_documento)])

        try:
            contabilizar_response = WOContabilizarDocumentoVentaResponse(**contabilizar_json)
        except ValidationError as e:
            exception = WOException(url=self.url, response=contabilizar_json, msg=str(e))
            wo_log.error(f'Error al contabilizar documento de venta: {exception}')
            raise exception

        if not contabilizar_response.valid():
            raise WOException(url=self.url, response=contabilizar_json)
        return True

    async def crear_tercero(self, wo_tercero_create: WOTerceroCreate) -> WOTercero:
        payload = wo_tercero_create.model_dump(exclude_none=True, exclude_unset=True, mode='json')
        tercero_json = await self.post(self.Paths.Terceros.crear, payload=payload)

        try:
            tercero_response = WOTerceroResponse(**tercero_json)
        except ValidationError as e:
            exception = WOException(url=self.url, payload=payload, response=tercero_json, msg=str(e))
            wo_log.error(f'Error al crear tercero: {exception}')
            raise exception

        if not tercero_response.data:
            raise WOException(url=self.url, payload=payload, response=tercero_json)
        return tercero_response.data

    async def editar_tercero(self, wo_tercero_edit: WOTerceroCreate) -> WOTercero:
        """_summary_
        Args:
            wo_tercero_edit (WOTerceroCreate): debe contar con el ID para editar el tercer.
        """
        payload = wo_tercero_edit.model_dump(exclude_none=True, exclude_unset=True, mode='json')
        if not wo_tercero_edit.id:
            raise WOException(
                payload=payload, msg='No se puede editar el tercero si no se proporciona un identificador'
            )
        tercero_json = await self.put(self.Paths.Terceros.editar, payload=payload)

        try:
            tercero_response = WOTerceroResponse(**tercero_json)
        except ValidationError as e:
            exception = WOException(url=self.url, payload=payload, response=tercero_json, msg=str(e))
            wo_log.error(f'Error al editar tercero: {exception}')
            raise exception

        if not tercero_response.valid():
            exception = WOException(url=self.url, payload=payload, response=tercero_json)
            wo_log.error(f'No se pudo editar tercero: {exception}')
            raise exception

        return tercero_response.data

    async def buscar_ciudad(self, departamento: str, ciudad: str | None) -> WOCiudad:
        valor = ciudad or departamento
        atributo = 'nombre' if ciudad else 'ubicacionDepartamento.nombre'
        filtro = WOFiltro(
            atributo=atributo,
            valor=valor,
            tipoFiltro=TipoFiltroWoFiltro.CONTIENE,
            tipoDato=TipoDatoWoFiltro.STRING,
            operador='AND',
        )

        wo_listar = WOListar(columnaOrdenar='id', registrosPorPagina=1, orden='ASC', filtros=[filtro])

        payload = wo_listar.model_dump(exclude_none=True, exclude_unset=True, mode='json')
        ciudades_json = await self.post(self.Paths.Ciudad.listar_ciudades, payload=payload)

        try:
            ciudades_response = WOListaCiudadesResponse(**ciudades_json)
        except ValidationError as e:
            exception = WOException(url=self.url, payload=payload, response=ciudades_json, msg=str(e))
            wo_log.error(f'Error al buscar ciudad: {exception}')
            raise exception

        # Si no se encuentra por nombre de ciudad, por posible escritura incorrecta, se busca por departamento.
        if not ciudades_response.valid():
            if valor == ciudad:
                atributo = 'ubicacionDepartamento.nombre'
                filtro.atributo = atributo
                filtro.valor = departamento

                wo_listar.filtros = [filtro]
                payload = wo_listar.model_dump(exclude_none=True, exclude_unset=True, mode='json')
                ciudades_json = await self.post(self.Paths.Ciudad.listar_ciudades, payload=payload)

                try:
                    ciudades_response = WOListaCiudadesResponse(**ciudades_json)
                except ValidationError as e:
                    exception = WOException(url=self.url, payload=payload, response=ciudades_json, msg=str(e))
                    wo_log.error(f'Error al buscar ciudad: {exception}')
                    raise exception

                if not ciudades_response.valid():
                    exception = WOException(url=self.url, payload=payload, response=ciudades_json)
                    wo_log.error(f'No se pudo buscar ciudad: {exception}')
                    raise exception

        return ciudades_response.data.content[0]

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
        wo_listar = WOListar(columnaOrdenar='id', registrosPorPagina=10, orden='ASC', filtros=[filtro1, filtro2])
        payload = wo_listar.model_dump(exclude_none=True, exclude_unset=True, mode='json')
        facturas_json = await self.post(self.Paths.Ventas.listar_documentos_venta, payload=payload)

        try:
            facturas_response = WOListaDocumentosVentaResponse(**facturas_json)
        except ValidationError as e:
            exception = WOException(url=self.url, payload=payload, response=facturas_json, msg=str(e))
            wo_log.error(f'Error al obtener lista de documentos de venta: {exception}')
            raise exception

        if not facturas_response.data.content:
            exception = WOException(url=self.url, payload=payload, response=facturas_json)
            wo_log.error(f'No se pudo obtener lista de documentos de venta: {exception}')
            raise exception

        return facturas_response.data.content[0]

    async def productos_documento_venta(self, id_documento: int) -> list[WOProductoDocumento]:
        wo_listar = WOListar(columnaOrdenar='id', registrosPorPagina=10, orden='ASC', filtros=[])
        payload = wo_listar.model_dump(exclude_none=True, exclude_unset=True, mode='json')
        productos_json = await self.post(
            self.Paths.Ventas.listar_productos,
            params=[str(id_documento)],
            payload=payload,
        )

        try:
            productos_response = WOListaProductosDocumentoVentaResponse(**productos_json)
        except ValidationError as e:
            exception = WOException(url=self.url, payload=payload, response=productos_json, msg=str(e))
            wo_log.error(f'Error al obtener lista de productos de documento de venta: {exception}')
            raise exception

        if not productos_response.data.content or len(productos_response.data.content) == 0:
            exception = WOException(url=self.url, payload=payload, response=productos_json)
            wo_log.error(f'No se pudo obtener lista de productos de documento de venta: {exception}')
            raise exception
        return productos_response.data.content

    async def crear_factura_venta(self, factura_create: WODocumentoVentaCreate):  # -> WODocumentoVentaDetail:
        payload = factura_create.model_dump(exclude_none=True, exclude_unset=True, mode='json')
        factura_dict = await self.post(self.Paths.Ventas.crear, payload=payload)

        try:
            factura_response = WODocumentoVentaDetailResponse(**factura_dict)
        except ValidationError as e:
            exception = WOException(url=self.url, payload=payload, response=factura_dict, msg=str(e))
            wo_log.error(f'Error al crear factura de venta: {exception}')
            raise exception

        if not factura_response.valid():
            exception = WOException(url=self.url, payload=payload, response=factura_dict)
            wo_log.error(f'No se pudo crear factura de venta: {exception}')
            raise exception
        return factura_response.data

    async def editar_factura_venta(self, factura_edit: WODocumentoVentaEdit) -> WODocumentoVentaDetail:
        payload = factura_edit.model_dump(exclude_none=True, exclude_unset=True, mode='json')
        factura_json = await self.put(self.Paths.Ventas.editar, payload=payload)

        try:
            factura_response = WODocumentoVentaDetailResponse(**factura_json)
        except ValidationError as e:
            exception = WOException(url=self.url, payload=payload, response=factura_json, msg=str(e))
            wo_log.error(f'Error al editar factura de venta: {exception}')
            raise exception

        if not factura_response.valid():
            exception = WOException(url=self.url, payload=payload, response=factura_json)
            wo_log.error(f'No se pudo editar factura de venta: {exception}')
            raise exception
        return factura_response.data


if __name__ == '__main__':
    from asyncio import run
    # from random import randint

    async def main():
        wo_client = WoClient()
        tercero = await wo_client.get_tercero('1094240554')
        assert tercero is not None and tercero.identificacion == '1094240554'
        ciudad = await wo_client.buscar_ciudad('Atlántico', 'Puerto Csolombia')
        print(ciudad)
        assert isinstance(ciudad, WOCiudad)
        factura = await wo_client.buscar_documento_venta(id_factura=31735)
        assert factura.id == 31735
        factura_detail = await wo_client.get_documento_venta(id_documento=31735)
        assert factura_detail.id == 31735
        productos_factura = await wo_client.productos_documento_venta(id_documento=31735)
        assert isinstance(productos_factura[0], WOProductoDocumento)
        inventario = await wo_client.get_inventario_por_codigo('COL-DES-MIRAMAR-60')
        assert isinstance(inventario, WOInventario)
        # documento_venta = await wo_client.crear_factura_venta(factura_create=WODocumentoVentaCreate())

    run(main())
