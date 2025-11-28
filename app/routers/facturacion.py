# app.routers.facturacion.py

from enum import Enum
from fastapi import APIRouter, Depends, HTTPException, status

from app.internal.gen.utilities import DateTz
from app.internal.integrations.world_office import WOException, WoClient
from app.models.pydantic.facturacion.invoice import Invoice
from app.models.pydantic.world_office.facturacion import WODocumentoCompraCreate, WODocumentoCompraTipo, WOReglone
from ..models.pydantic.world_office.general import WOCiudad
from app.models.pydantic.world_office.terceros import ResponsabilidadFiscal, WODireccion, WOTerceroCreateEdit


if __name__ == '__main__':
    from os.path import abspath
    from sys import path as sys_path

    sys_path.append(abspath('.'))


from app.internal.log import LogLevel, factory_logger


# Base de datos (Repositorio)
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.db.session import get_async_session
from app.models.db.transacciones import Compra, CompraCreate
from app.internal.query.transacciones import TransaccionQuery
import traceback

from app.routers.auth import validar_access_token

log_inventario = factory_logger('facturacion', file=True)
log_debug = factory_logger('debug', level=LogLevel.DEBUG, file=False)

compra_query = TransaccionQuery(Compra, CompraCreate)


class Tags(Enum):
    INVENTARIO = 'Facturacion'


router = APIRouter(
    prefix='/facturacion',
    tags=[Tags.INVENTARIO],
    responses={404: {'description': 'No encontrado'}},
    dependencies=[Depends(validar_access_token)],
)


@router.post(
    '/compra',
    status_code=status.HTTP_200_OK,
    response_model=bool,
    summary='Genera una factura de compra.',
    description='A partir de los datos extraidos de una factura electrónica válida, se genera una factura de compra.',
    tags=[Tags.INVENTARIO],
    dependencies=[Depends(validar_access_token)],
)
async def facturar_compra_invoice(invoice: Invoice, session: AsyncSession = Depends(get_async_session)) -> bool:
    # 0. Se crea el registro de la compra en la base de datos, se usa el uuid por si llega a coincidir el secuencial de la factura de diferentes proveedores.
    compra_id = f'{invoice.id} {invoice.uuid}'
    compra = await compra_query.get_by_number(session, compra_id)
    if not compra:
        compra_create = CompraCreate(numero_factura_proveedor=compra_id)
        compra = await compra_query.create(session, compra_create)

    if compra.factura_id:
        return True

    try:
        # region tercero
        # 1. Se debe crear el tercero de la factura, si No está creado previamente.
        # Con base en el tercero WO calcula los impuestos, retenciones correctas.
        # - Si el tercero ya existe, se debe validar que sea un porveedor (id timpo tercero proveedor => 6), si no lo es modificarlo.
        # 2. Se debe validar si el tercero tiene dirección principal para facturar.
        wo_client = WoClient()
        wo_tercero = await wo_client.get_tercero(invoice.emisor.documento)
        wo_ciudad = await wo_client.buscar_ciudad(codigo=invoice.emisor.ciudad_id)
        if isinstance(wo_ciudad, WOException):
            raise HTTPException(status_code=404, detail=str(wo_ciudad))

        direcciones = [
            WODireccion(
                nombre='Principal',
                direccion=invoice.emisor.address,
                senPrincipal=True,
                emailPrincipal=invoice.emisor.email,
                telefonoPrincipal=invoice.emisor.telefono,
                ubicacionCiudad=WOCiudad(
                    id=wo_ciudad.id,
                ),
            )
        ]

        responsabilidades_emisor = invoice.emisor.responsabilidadesfiscales.split(';')
        responsabilidades_emisor = [ResponsabilidadFiscal.buscar(x) for x in responsabilidades_emisor]

        wo_tercero_create = WOTerceroCreateEdit(
            idTerceroTipoIdentificacion=6,  # NIT
            identificacion=invoice.emisor.documento,
            primerNombre=invoice.emisor.nombrecomercial or invoice.emisor.razonsocial,
            idCiudad=wo_ciudad.id,
            direccion=invoice.emisor.address,
            direcciones=direcciones,
            idTerceroTipos=[6],  # Proveedor
            idTerceroTipoContribuyente=6,
            idClasificacionImpuestos=1,
            telefono=invoice.emisor.telefono,
            email=invoice.emisor.email,
            plazoDias=30,
            responsabilidadFiscal=responsabilidades_emisor,
        )

        if wo_tercero is None:
            wo_tercero = await wo_client.crear_tercero(wo_tercero_create)
        elif not wo_tercero.is_provider():
            wo_tercero_create.id = wo_tercero.id  # Id necesario para que se realice la actualización de forma correcta.
            wo_tercero_create.idTerceroTipoIdentificacion = wo_tercero.terceroTipoIdentificacion.id
            wo_tercero_create.idTerceroTipos = wo_tercero.idTerceroTipos + [6]  # Proveedor
            wo_tercero = await wo_client.editar_tercero(wo_tercero_create)  # endregion tercero

        # endregion tercero

        # region reglone
        # 1. Se debe buscar el id del  prodcuto a facturar
        wo_reglones = []
        for item in invoice.lineitems:
            if not item.inventario and not item.cuenta:
                raise HTTPException(
                    status_code=404, detail=f'El item {item.nombre} no cuenta con inventario ni cuenta contable'
                )

            id_inventario = None

            if item.inventario:
                wo_producto = await wo_client.get_inventario_por_codigo(item.inventario)
                if isinstance(wo_producto, WOException):
                    raise HTTPException(status_code=404, detail=str(wo_producto))
                id_inventario = wo_producto.id
            else:
                wo_producto = await wo_client.get_inventario_por_codigo(item.cuenta)
                if isinstance(wo_producto, WOException):
                    raise HTTPException(status_code=404, detail=str(wo_producto))
                id_inventario = wo_producto.id

            # Si el producto tiene IVA, usar el valor sin IVA que está en los impuestos
            valor_unitario = item.valorunitario
            # Cantidad y valor base -> En el invoice el impuesto viene totalizado por producto, no por unidad, por lo cúal el valor base se debe dividir en la catidad de unidades.
            cantidad = float(item.kg) if item.kg else float(item.und)
            if len(item.impuestos) > 0:
                valor_unitario = item.impuestos[0].base / cantidad

            # 1 Es la única bodega disponible por defecto para cuentas de gasto, para inventario bodega 3
            id_bodega = 3 if item.inventario else 1

            wo_reglone = WOReglone(
                idInventario=id_inventario,
                unidadMedida='kg' if item.kg else 'und',  # kg solo se asigna si el item es un inventario por agente
                cantidad=cantidad,
                valorUnitario=valor_unitario,
                idBodega=id_bodega,
                porDescuento=0,
            )

            wo_reglones.append(wo_reglone)

        # endregion reglone

        factura_compra = await wo_client.crear_factura_compra(
            WODocumentoCompraCreate(
                fecha=DateTz.from_str(invoice.fecha),
                prefijo=1,  # TODO: 1 -> Sin Prefijo, Cambiar para producción
                documentoTipo=WODocumentoCompraTipo.FACTURA_COMPRA,
                concepto=f'FACTURA DE COMPRA - {invoice.id}',
                idEmpresa=1,
                idTerceroExterno=wo_tercero.id,
                idTerceroInterno=1,
                idFormaPago=5,
                idMoneda=31,
                porcentajeDescuento=True,
                reglones=wo_reglones,
            )
        )

        # Al contabilizar documento, realiza la contabilización del documento
        contabilizado = await wo_client.contabilizar_documento(wo_client.Paths.Compras.contabilizar, factura_compra.id)

        # region log success
        compra_update = compra.model_copy()
        compra_update.factura_id = factura_compra.id
        compra_update.factura_numero = factura_compra.numero
        compra_update.contabilizado = contabilizado
        compra_update.log = None
        await compra_query.update(session, compra_update, compra.id)
        # endregion log success

        return contabilizado

    except WOException as e:
        # region log error
        compra_update = compra.model_copy()
        compra_update.log = str(e)
        await compra_query.update(session, compra_update, compra.id)
        raise e
        # endregion log error
    except Exception as e:
        # region log error
        compra_update = compra.model_copy()
        compra_update.log = str(e) if str(e) else traceback.format_exc()
        await compra_query.update(session, compra_update, compra.id)
        raise e
        # endregion log error


if __name__ == '__main__':
    from asyncio import run
    # from app.models.db.session import get_async_session

    async def main(): ...

    run(main())
