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
        super().__init__(min_interval=1)
        self.host = host
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'WO {config.wo_api_key}',
        }

    async def get_tercero(self, identificacion: str) -> WOTercero | None:
        if not identificacion:
            msg = 'Falta documento de identidad'
            exception = WOException(msg=msg)
            wo_log.error(str(exception))
            raise exception

        url = self.build_url(self.host, self.Paths.Terceros.identificacion, [identificacion])
        tercero_json = await self.request('GET', self.headers, url)

        try:
            tercero_response = WOTerceroResponse(**tercero_json)
        except ValidationError as e:
            msg = f'{type(e)} {WOTerceroResponse.__name__}, id: {identificacion}'
            msg += f'\n{repr(e.errors())}'
            exception = WOException(url=url, response=tercero_json, msg=msg)
            wo_log.error(str(exception))
            raise exception

        if tercero_response.valid():
            if not tercero_response.data.id:
                return None
        else:
            msg = f'No se encontró tercero, identificación: {identificacion}'
            exception = WOException(url=url, response=tercero_json, msg=msg)
            wo_log.error(str(exception))
            raise exception

        return tercero_response.data

    async def get_documento_venta(self, id_documento: int) -> WODocumentoVentaDetail:
        url = self.build_url(self.host, self.Paths.Ventas.documento_venta, [str(id_documento)])
        documento_venta_json = await self.request('GET', self.headers, url)

        try:
            documento_venta_response = WODocumentoVentaDetailResponse(**documento_venta_json)
        except ValidationError as e:
            msg = f'{type(e)} {WODocumentoVentaDetailResponse.__name__}, id: {id_documento}'
            msg += f'\n{repr(e.errors())}'
            exception = WOException(url=url, response=documento_venta_json, msg=msg)
            wo_log.error(str(exception))
            raise exception

        if not documento_venta_response.data:
            msg = f'No se encontró documento de venta, id: {id_documento}'
            exception = WOException(url=url, response=documento_venta_json, msg=msg)
            wo_log.error(str(exception))
            raise exception

        return documento_venta_response.data

    async def get_inventario_por_codigo(self, codigo: str) -> WOInventario:
        url = self.build_url(self.host, self.Paths.Inventario.inventario_por_codigo, [codigo])
        inventario_json = await self.request('GET', self.headers, url)

        try:
            inventario_response = WOInventarioResponse(**inventario_json)
        except ValidationError as e:
            msg = f'{type(e)} {WOInventarioResponse.__name__}, codigo: {codigo}'
            msg += f'\n{repr(e.errors())}'
            exception = WOException(url=url, response=inventario_json, msg=msg)
            wo_log.error(str(exception))
            raise exception

        if not inventario_response.valid():
            msg = 'No se obtuvo inventario'
            exception = WOException(url=url, response=inventario_json, msg=msg)
            wo_log.error(str(exception))
            raise exception

        return inventario_response.data

    async def contabilizar_documento_venta(self, id_documento: int) -> bool:
        url = self.build_url(self.host, self.Paths.Ventas.contabilizar, [str(id_documento)])
        contabilizar_json = await self.request('POST', self.headers, url)

        try:
            contabilizar_response = WOContabilizarDocumentoVentaResponse(**contabilizar_json)
        except ValidationError as e:
            msg = f'{type(e)} {WOContabilizarDocumentoVentaResponse.__name__}, id: {id_documento}'
            msg += f'\n{repr(e.errors())}'
            exception = WOException(url=url, response=contabilizar_json, msg=msg)
            wo_log.error(str(exception))
            raise exception

        if not contabilizar_response.valid():
            msg = 'No se contabilizó documento de venta'
            exception = WOException(url=url, response=contabilizar_json, msg=msg)
            wo_log.error(str(exception))
            raise exception

        return True

    async def crear_tercero(self, wo_tercero_create: WOTerceroCreate) -> WOTercero:
        url = self.build_url(self.host, self.Paths.Terceros.crear)
        payload = wo_tercero_create.model_dump(exclude_none=True, exclude_unset=True, mode='json')
        tercero_json = await self.request('POST', self.headers, url, payload=payload)

        try:
            tercero_response = WOTerceroResponse(**tercero_json)
        except ValidationError as e:
            msg = f'{type(e)} {WOTerceroResponse.__name__}, id: {wo_tercero_create.id}'
            msg += f'\n{repr(e.errors())}'
            exception = WOException(url=url, payload=payload, response=tercero_json, msg=msg)
            wo_log.error(str(exception))
            raise exception

        if not tercero_response.data:
            msg = 'No se creó tercero'
            exception = WOException(url=url, payload=payload, response=tercero_json, msg=msg)
            wo_log.error(str(exception))
            raise exception
        return tercero_response.data

    async def editar_tercero(self, wo_tercero_edit: WOTerceroCreate) -> WOTercero:
        """_summary_
        Args:
            wo_tercero_edit (WOTerceroCreate): debe contar con el ID para editar el tercer.
        """
        url = self.build_url(self.host, self.Paths.Terceros.editar)
        payload = wo_tercero_edit.model_dump(exclude_none=True, exclude_unset=True, mode='json')
        if not wo_tercero_edit.id:
            msg = 'Identificador requerido.'
            exception = WOException(payload=payload, msg=msg)
            wo_log.error(str(exception))
            raise exception

        tercero_json = await self.request('PUT', self.headers, url, payload=payload)

        try:
            tercero_response = WOTerceroResponse(**tercero_json)
        except ValidationError as e:
            msg = f'{type(e)} {WOTerceroResponse.__name__}, id: {wo_tercero_edit.id}'
            msg += f'\n{repr(e.errors())}'
            exception = WOException(url=url, payload=payload, response=tercero_json, msg=msg)
            wo_log.error(str(exception))
            raise exception

        if not tercero_response.valid():
            msg = 'No se editó tercero'
            exception = WOException(url=url, payload=payload, response=tercero_json, msg=msg)
            wo_log.error(str(exception))
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

        url = self.build_url(self.host, self.Paths.Ciudad.listar_ciudades)
        payload = wo_listar.model_dump(exclude_none=True, exclude_unset=True, mode='json')

        try:
            ciudades_json = await self.request('POST', self.headers, url, payload=payload)
        except Exception as e:
            msg = f'{type(e)}, ciudad: {ciudad}, departamento: {departamento}'
            exception = WOException(url=url, payload=payload, response=None, msg=msg)
            wo_log.error(f'{exception}')
            raise exception

        try:
            ciudades_response = WOListaCiudadesResponse(**ciudades_json)
        except ValidationError as e:
            msg = f'ValidarionError, ciudad: {ciudad}, departamento: {departamento}'
            msg += f'\n{repr(e.errors())}'
            exception = WOException(url=url, payload=payload, response=ciudades_json, msg=msg)
            wo_log.error(str(exception))
            ciudades_response = WOListaCiudadesResponse()

        # Si no se encuentra por nombre de ciudad, por posible escritura incorrecta, se busca por departamento.
        if not ciudades_response.valid():
            if valor == ciudad:
                atributo = 'ubicacionDepartamento.nombre'
                filtro.atributo = atributo
                filtro.valor = departamento

                wo_listar.filtros = [filtro]
                url = self.build_url(self.host, self.Paths.Ciudad.listar_ciudades)
                payload = wo_listar.model_dump(exclude_none=True, exclude_unset=True, mode='json')
                ciudades_json = await self.request('POST', self.headers, url, payload=payload)

                try:
                    ciudades_response = WOListaCiudadesResponse(**ciudades_json)
                except ValidationError as e:
                    msg = (
                        f'{type(e)} {WOListaCiudadesResponse.__name__}, ciudad: {ciudad}, departamento: {departamento}'
                    )
                    msg += f'\n{repr(e.errors())}'
                    exception = WOException(url=url, payload=payload, response=ciudades_json, msg=msg)
                    wo_log.error(str(exception))
                    raise exception

                if not ciudades_response.valid():
                    msg = 'No se encontró ciudad, ciudad: {ciudad}, departamento: {departamento}'
                    exception = WOException(url=url, payload=payload, response=ciudades_json, msg=msg)
                    wo_log.error(str(exception))
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
        url = self.build_url(self.host, self.Paths.Ventas.listar_documentos_venta)
        payload = wo_listar.model_dump(exclude_none=True, exclude_unset=True, mode='json')
        facturas_json = await self.request('POST', self.headers, url, payload=payload)

        try:
            facturas_response = WOListaDocumentosVentaResponse(**facturas_json)
        except ValidationError as e:
            msg = f'{type(e)} {WOListaDocumentosVentaResponse.__name__}, id: {id_factura}'
            msg += f'\n{repr(e.errors())}'
            exception = WOException(url=url, payload=payload, response=facturas_json, msg=msg)
            wo_log.error(str(exception))
            raise exception

        if not facturas_response.data.content:
            msg = f'No se encontró documento de venta, id: {id_factura}'
            exception = WOException(url=url, payload=payload, response=facturas_json, msg=msg)
            wo_log.error(str(exception))
            raise exception

        return facturas_response.data.content[0]

    async def productos_documento_venta(self, id_documento: int) -> list[WOProductoDocumento]:
        wo_listar = WOListar(columnaOrdenar='id', registrosPorPagina=10, orden='ASC', filtros=[])
        url = self.build_url(self.host, self.Paths.Ventas.listar_productos, [str(id_documento)])
        payload = wo_listar.model_dump(exclude_none=True, exclude_unset=True, mode='json')
        productos_json = await self.request('POST', self.headers, url, payload=payload)

        try:
            productos_response = WOListaProductosDocumentoVentaResponse(**productos_json)
        except ValidationError as e:
            msg = f'{type(e)} {WOListaProductosDocumentoVentaResponse.__name__}, id: {id_documento}'
            msg += f'\n{repr(e.errors())}'
            exception = WOException(url=url, payload=payload, response=productos_json, msg=msg)
            wo_log.error(str(exception))
            raise exception

        if not productos_response.data.content or len(productos_response.data.content) == 0:
            msg = f'No se encontrarón productos para el de documento de venta, id: {id_documento}'
            exception = WOException(url=url, payload=payload, response=productos_json, msg=msg)
            wo_log.error(str(exception))
            raise exception
        return productos_response.data.content

    async def crear_factura_venta(self, factura_create: WODocumentoVentaCreate):  # -> WODocumentoVentaDetail:
        url = self.build_url(self.host, self.Paths.Ventas.crear)
        payload = factura_create.model_dump(exclude_none=True, exclude_unset=True, mode='json')
        factura_dict = await self.request('POST', self.headers, url, payload=payload, timeout=60)

        try:
            factura_response = WODocumentoVentaDetailResponse(**factura_dict)
        except ValidationError as e:
            msg = f'{type(e)} {WODocumentoVentaDetailResponse.__name__}'
            msg += f'\n{repr(e.errors())}'
            exception = WOException(url=url, payload=payload, response=factura_dict, msg=msg)
            wo_log.error(str(exception))
            raise exception

        if not factura_response.valid():
            msg = 'No se creó factura de venta'
            exception = WOException(url=url, payload=payload, response=factura_dict, msg=msg)
            wo_log.error(str(exception))
            raise exception

        return factura_response.data

    async def editar_factura_venta(self, factura_edit: WODocumentoVentaEdit) -> WODocumentoVentaDetail:
        url = self.build_url(self.host, self.Paths.Ventas.editar)
        payload = factura_edit.model_dump(exclude_none=True, exclude_unset=True, mode='json')
        factura_json = await self.request('PUT', self.headers, url, payload=payload)

        try:
            factura_response = WODocumentoVentaDetailResponse(**factura_json)
        except ValidationError as e:
            msg = f'{type(e)} {WODocumentoVentaDetailResponse.__name__}, id: {factura_edit.id}'
            msg += f'\n{repr(e.errors())}'
            exception = WOException(url=url, payload=payload, response=factura_json, msg=msg)
            wo_log.error(str(exception))
            raise exception

        if not factura_response.valid():
            msg = 'No se editó factura de venta'
            exception = WOException(url=url, payload=payload, response=factura_json, msg=msg)
            wo_log.error(str(exception))
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
