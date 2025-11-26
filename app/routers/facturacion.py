# app/routers/inventario.py
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
from app.routers.auth import validar_access_token

log_inventario = factory_logger('facturacion', file=True)
log_debug = factory_logger('debug', level=LogLevel.DEBUG, file=False)


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
    summary='Genera una factura de compra.',
    description='A partir de los datos extraidos de una factura electrónica válida, se genera una factura de compra.',
    tags=[Tags.INVENTARIO],
    dependencies=[Depends(validar_access_token)],
)
async def facturar_compra_invoice(invoice: Invoice):
    # region tercero
    # 1. Se debe crear el tercero de la factura, si No está creado previamente.
    # Con base en el tercero WO calcula los impuestos, retenciones correctas.
    # - Si el tercero ya existe, se debe validar que sea un porveedor (id timpo tercero proveedor => 6), si no lo es modificarlo.
    # 2. Se debe validar si el tercero tiene dirección principal para facturar.
    wo_client = WoClient()
    wo_tercero = await wo_client.get_tercero(invoice.emisor.documento)
    wo_ciudad = await wo_client.buscar_ciudad(invoice.emisor.ciudad, invoice.emisor.departamento)
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
        wo_producto = await wo_client.get_inventario_por_codigo(item.inventario)
        if isinstance(wo_producto, WOException):
            raise HTTPException(status_code=404, detail=str(wo_producto))
        # Si el producto tiene IVA, usar el valor sin IVA que está en los impuestos
        valor_unitario = item.valorunitario
        if len(wo_producto.impuestos) > 0:
            valor_unitario = item.impuestos[0].base

        wo_reglone = WOReglone(
            idInventario=wo_producto.id,
            unidadMedida='kg' if item.kg else 'und',  # kg solo se asigna si el item es un inventario por agente
            cantidad=float(item.kg) if item.kg else float(item.und),
            valorUnitario=valor_unitario,
            idBodega=3, # Bodega insumos
            porDescuento=0,
        )

        wo_reglones.append(wo_reglone)

    # endregion reglone

    await wo_client.crear_factura_compra(
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


if __name__ == '__main__':
    from asyncio import run
    # from app.models.db.session import get_async_session

    async def main():
        ...

    run(main())
