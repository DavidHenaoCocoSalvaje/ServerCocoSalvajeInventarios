# app.internal.integrations.world_office

if __name__ == '__main__':
    from os.path import abspath
    from sys import path as sys_path

    sys_path.append(abspath('.'))

# from random import randint


from pydantic import ValidationError
from app.internal.log import factory_logger
from app.models.pydantic.world_office.base import Operador, TipoDatoWoFiltro, TipoFiltroWoFiltro, WOFiltro, WOListar
from app.models.pydantic.world_office.invenvario import WOListaInventariosResponse, WODataListInventarios
from app.models.pydantic.world_office.facturacion import (
    WOContabilizarFacturaResponse,
    WODocumentoCompraCreate,
    WODocumentoCompraResponse,
    WODocumentoFactura,
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
from app.models.pydantic.world_office.terceros import WOTercero, WOTerceroResponse, WOTerceroCreateEdit
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

        class Compras:
            root: str = '/compra'
            crear: str = f'{root}/crearCompra'
            contabilizar = f'{root}/contabilizarCompra'

        class Ciudad:
            root: str = '/ciudad'
            listar_ciudades: str = f'{root}/listarCiudades'

        class Inventario:
            root: str = '/inventarios'
            inventario_por_codigo: str = f'{root}/consultaCodigo'
            listar_inventarios: str = f'{root}/listarInventarios'

    # Singleton para implementar posteriormente la restricción de peticiones.
    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self, host: str = f'https://api.worldoffice.cloud/api/{config.wo_api_version}'):
        super().__init__(min_interval=1)
        self.host = host
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'WO {config.wo_api_key}',
        }

    # Se han obtenido varios timeouts usando 30 segundos. se cambia a 60 segundos.
    async def request(
        self,
        method: str,
        headers: dict,
        url: str,
        payload: dict | None = None,
        timeout: int = 60,
        cookies: dict | None = None,
    ):
        return await super().request(method, headers, url, payload, timeout=timeout, cookies=cookies)

    async def get_tercero(self, identificacion: str) -> WOTercero | None:
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

    async def get_list_inventario_por_codigo(self, codigo: str) -> WODataListInventarios:
        url = self.build_url(self.host, self.Paths.Inventario.listar_inventarios)

        wo_filtro = WOFiltro(
            atributo='codigo',
            valor=codigo,
            valor2=None,
            tipoFiltro=TipoFiltroWoFiltro.CONTIENE,
            tipoDato=TipoDatoWoFiltro.STRING,
            nombreColumna='',
            valores=None,
            clase='',
            operador=Operador.AND,
            subGrupo='filtro',
        )
        wo_listar = WOListar(
            columnaOrdenar='id',
            pagina=0,
            registrosPorPagina=10,
            orden='DESC',
            filtros=[wo_filtro],
            canal=0,
            registroInicial=0,
        )
        payload = wo_listar.model_dump(exclude_none=True, exclude_unset=True, mode='json')

        try:
            inventarios_json = await self.request('POST', self.headers, url, payload=payload)
        except Exception as e:
            msg = f'{type(e)}, codigo: {codigo}'
            exception = WOException(url=url, payload=payload, response=None, msg=msg)
            wo_log.error(f'{exception}')
            raise exception

        try:
            inventarios_response = WOListaInventariosResponse(**inventarios_json)
        except ValidationError as e:
            msg = f'{type(e)} {WOListaInventariosResponse.__name__}, codigo: {codigo}'
            msg += f'\n{repr(e.errors())}'
            exception = WOException(url=url, response=inventarios_json, msg=msg)
            wo_log.error(str(exception))
            raise exception

        if not inventarios_response.valid():
            msg = 'No se obtuvo inventario'
            exception = WOException(url=url, payload=payload, response=inventarios_json, msg=msg)
            wo_log.error(str(exception))
            raise exception

        return inventarios_response.data

    async def contabilizar_documento(self, path: str, id_documento: int) -> bool:
        url = self.build_url(self.host, path, [str(id_documento)])
        contabilizar_json = await self.request('POST', self.headers, url)

        try:
            contabilizar_response = WOContabilizarFacturaResponse(**contabilizar_json)
        except ValidationError as e:
            msg = f'{type(e)} {WOContabilizarFacturaResponse.__name__}, id: {id_documento}'
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

    async def crear_tercero(self, wo_tercero_create: WOTerceroCreateEdit) -> WOTercero:
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

    async def editar_tercero(self, wo_tercero_edit: WOTerceroCreateEdit) -> WOTercero:
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

    async def buscar_ciudad(
        self, nombre: str | None = None, departamento: str | None = None, codigo: str | None = None
    ) -> WOCiudad:
        if nombre:
            atributo = 'nombre'
            valor = nombre
        elif departamento:
            atributo = 'ubicacionDepartamento.nombre'
            # En Shopify sale como Archipiélago de San Andrés, Providencia y Santa Catalina, pero en World Office es Archipiélago de San Andrés.
            valor = (
                'Archipiélago de San Andrés'
                if departamento == 'San Andrés, Providencia y Santa Catalina'
                else departamento
            )
        elif codigo:
            atributo = 'codigo'
            valor = codigo
        else:
            exception = WOException(msg='No se proporcionó nombre, departamento o código para buscar ciudad')
            raise exception

        filtro = WOFiltro(
            atributo=atributo,
            valor=valor,
            tipoFiltro=TipoFiltroWoFiltro.IGUAL,
            tipoDato=TipoDatoWoFiltro.STRING,
            operador=Operador.AND,
        )

        wo_listar = WOListar(columnaOrdenar='id', registrosPorPagina=1, orden='ASC', filtros=[filtro])
        url = self.build_url(self.host, self.Paths.Ciudad.listar_ciudades)
        payload = wo_listar.model_dump(exclude_none=True, exclude_unset=True, mode='json')

        try:
            ciudades_json = await self.request('POST', self.headers, url, payload=payload)
        except Exception as e:
            msg = f'{type(e)}, ciudad: {nombre}'
            exception = WOException(url=url, payload=payload, response=None, msg=msg)
            wo_log.error(f'{exception}')
            raise exception

        try:
            ciudades_response = WOListaCiudadesResponse(**ciudades_json)
        except ValidationError as e:
            msg = f'ValidarionError, ciudad: {nombre}'
            msg += f'\n{repr(e.errors())}'
            exception = WOException(url=url, payload=payload, response=ciudades_json, msg=msg)
            raise exception

        if not ciudades_response.valid():
            msg = 'No se encontró ciudad'
            if nombre:
                msg += f', nombre: {nombre}'
            if departamento:
                msg += f', departamento: {departamento}'
            exception = WOException(url=url, payload=payload, response=ciudades_json, msg=msg)
            raise exception

        return ciudades_response.data.content[0]

    async def documento_venta_por_concepto(self, concepto: str, codigo_documento: str = 'FV') -> WODocumentoFactura:
        # Filtro1 Obligatorio de acuerdo a la documentación de World Office
        filtro1 = WOFiltro(
            atributo='documentoTipo.codigoDocumento',
            valor=codigo_documento,
            tipoFiltro=TipoFiltroWoFiltro.IGUAL,
            tipoDato=TipoDatoWoFiltro.STRING,
            operador=Operador.AND,
        )
        filtro2 = WOFiltro(
            atributo='concepto',
            valor=concepto,
            tipoFiltro=TipoFiltroWoFiltro.IGUAL,
            tipoDato=TipoDatoWoFiltro.STRING,
            operador=Operador.AND,
        )
        wo_listar = WOListar(columnaOrdenar='id', registrosPorPagina=10, orden='ASC', filtros=[filtro1, filtro2])
        url = self.build_url(self.host, self.Paths.Ventas.listar_documentos_venta)
        payload = wo_listar.model_dump(exclude_none=True, exclude_unset=True, mode='json')
        facturas_json = await self.request('POST', self.headers, url, payload=payload)

        try:
            facturas_response = WOListaDocumentosVentaResponse(**facturas_json)
        except ValidationError as e:
            msg = f'{type(e)} {WOListaDocumentosVentaResponse.__name__}, concepto: {concepto}'
            msg += f'\n{repr(e.errors())}'
            exception = WOException(url=url, payload=payload, response=facturas_json, msg=msg)
            wo_log.error(str(exception))
            raise exception

        if not facturas_response.data.content:
            msg = f'No se encontró documento de venta, concepto: {concepto}'
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

    async def crear_factura_venta(self, documento_venta_create: WODocumentoVentaCreate) -> WODocumentoVentaDetail:
        url = self.build_url(self.host, self.Paths.Ventas.crear)
        payload = documento_venta_create.model_dump(exclude_none=True, exclude_unset=True, mode='json')
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

    async def editar_factura_venta(self, documento_venta_edit: WODocumentoVentaEdit) -> WODocumentoVentaDetail:
        url = self.build_url(self.host, self.Paths.Ventas.editar)
        payload = documento_venta_edit.model_dump(exclude_none=True, exclude_unset=True, mode='json')
        factura_json = await self.request('PUT', self.headers, url, payload=payload)

        try:
            factura_response = WODocumentoVentaDetailResponse(**factura_json)
        except ValidationError as e:
            msg = f'{type(e)} {WODocumentoVentaDetailResponse.__name__}, id: {documento_venta_edit.id}'
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

    async def crear_factura_compra(self, documento_compra_create: WODocumentoCompraCreate) -> WODocumentoFactura:
        url = self.build_url(self.host, self.Paths.Compras.crear)
        payload = documento_compra_create.model_dump(exclude_none=True, exclude_unset=True, mode='json')
        factura_json = await self.request('POST', self.headers, url, payload=payload)

        try:
            factura_response = WODocumentoCompraResponse(**factura_json)
        except ValidationError as e:
            msg = f'{type(e)} {WODocumentoCompraResponse.__name__}'
            msg += f'\n{repr(e.errors())}'
            exception = WOException(url=url, payload=payload, response=factura_json, msg=msg)
            wo_log.error(str(exception))
            raise exception

        if not factura_response.valid():
            msg = 'No se creó factura de compra'
            exception = WOException(url=url, payload=payload, response=factura_json, msg=msg)
            wo_log.error(str(exception))
            raise exception
        return factura_response.data


if __name__ == '__main__':
    from asyncio import run
    # from random import randint
    # from app.internal.gen.utilities import DateTz
    # from app.models.pydantic.world_office.facturacion import WOReglone, WODocumentoCompraTipo

    async def main():
        wo_client = WoClient()
        # tercero = await wo_client.get_tercero('1094240554')
        # assert tercero is not None and tercero.identificacion == '1094240554'
        # ciudad = await wo_client.buscar_ciudad('Atlántico', 'Puerto Csolombia')
        # assert isinstance(ciudad, WOCiudad)
        # factura = await wo_client.documento_venta_por_concepto('Factura de venta')
        # assert factura.id == 31735
        # factura_detail = await wo_client.get_documento_venta(id_documento=31735)
        # assert factura_detail.id == 31735
        # productos_factura = await wo_client.productos_documento_venta(id_documento=31735)
        # assert isinstance(productos_factura[0], WOProductoDocumento)
        # inventario = await wo_client.get_inventario_por_codigo('COL-DES-MIRAMAR-60')
        # assert isinstance(inventario, WOInventario)

        # {
        #     "fecha": "2025-11-20",
        #     "prefijo": 1,
        #     "documentoTipo": "FC",
        #     "concepto": "FACTURA DE COMPRA PRUEBA",
        #     "idEmpresa": 1,
        #     "idTerceroExterno": 11208,
        #     "idTerceroInterno": 1,
        #     "idFormaPago": 5,
        #     "idMoneda": 31,
        #     "porcentajeDescuento": true,
        #     "reglones": [
        #         {
        #         "idInventario": 1243,
        #         "unidadMedida": "kg",
        #         "cantidad": 100,
        #         "valorUnitario": 10000,
        #         "idBodega": 3,
        #         "porDescuento": 0
        #         }
        #     ]
        # }
        # factura_compra = await wo_client.crear_factura_compra(
        #     WODocumentoCompraCreate(
        #         fecha=DateTz.today(),
        #         prefijo=1,
        #         documentoTipo=WODocumentoCompraTipo.FACTURA_COMPRA,
        #         concepto='FACTURA DE COMPRA PRUEBA',
        #         idEmpresa=1,
        #         idTerceroExterno=11208,
        #         idTerceroInterno=1,
        #         idFormaPago=5,
        #         idMoneda=31,
        #         porcentajeDescuento=True,
        #         reglones=[
        #             WOReglone(
        #                 idInventario='1243',
        #                 unidadMedida='kg',
        #                 cantidad=100,
        #                 valorUnitario=10000,
        #                 idBodega=3,
        #                 porDescuento=0,
        #             )
        #         ],
        #     )
        # )
        # print(factura_compra.model_dump_json(indent=4))
        # {
        #   "columnaOrdenar": "id",
        #   "pagina": 0,
        #   "registrosPorPagina": 10,
        #   "orden": "DESC",
        #   "filtros": [
        #     {
        #       "atributo": "codigo",
        #       "valor": "529525",
        #       "valor2": null,
        #       "tipoFiltro": 1,
        #       "tipoDato": 0,
        #       "nombreColumna": "",
        #       "valores": null,
        #       "clase": "",
        #       "operador": 0,
        #       "subGrupo": "filtro"
        #     }
        #   ],
        #   "canal": 0,
        #   "registroInicial": 0
        # }

        inventario = await wo_client.get_list_inventario_por_codigo('529525')
        print(inventario.model_dump_json(indent=4))

    run(main())
