# app.routers.facturacion.py
if __name__ == '__main__':
    from os.path import abspath
    from sys import path as sys_path

    sys_path.append(abspath('.'))

from enum import Enum
import json
from fastapi import APIRouter, Depends, HTTPException, status

from app.internal.gen.utilities import DateTz
from app.internal.integrations.world_office import WOException, WoClient
from app.internal.query.transacciones import CompraQuery
from app.models.db.transacciones import CompraCreate
from app.models.pydantic.facturacion.invoice import Invoice
from app.models.pydantic.world_office.facturacion import WODocumentoCompraCreate, WODocumentoCompraTipo, WOReglone
from app.models.pydantic.world_office.general import WOCiudad
from app.models.pydantic.world_office.terceros import ResponsabilidadFiscal, WODireccion, WOTerceroCreateEdit


if __name__ == '__main__':
    from os.path import abspath
    from sys import path as sys_path

    sys_path.append(abspath('.'))


from app.internal.log import LogLevel, factory_logger


# Base de datos (Repositorio)
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.db.session import get_async_session
import traceback

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


@router.get(
    '/compra-contabilizada',
    status_code=status.HTTP_200_OK,
    response_model=bool,
    summary='Verifica si una compra ha sido contabilizada.',
    description='Verifica si una compra ha sido contabilizada.',
    tags=[Tags.INVENTARIO],
    dependencies=[Depends(validar_access_token)],
)
async def compra_contabilizada(compra_provider_number: str, session: AsyncSession = Depends(get_async_session)) -> bool:
    compra_query = CompraQuery()
    compra = await compra_query.get_by_provider_number(session, compra_provider_number)
    return compra is not None and compra.factura_id is not None


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
    compra_query = CompraQuery()
    # 0. Se crea el registro de la compra en la base de datos, se usa el uuid por si llega a coincidir el secuencial de la factura de diferentes proveedores.
    compra_provider_number = f'{invoice.id} {invoice.uuid}'
    compra = await compra_query.get_by_provider_number(session, compra_provider_number)
    if not compra:
        compra_create = CompraCreate(numero_factura_proveedor=compra_provider_number)
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
            primerApellido=' ',  # WO Exige el campo primer apellido al usar el api v1.
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
                wo_inventarios = await wo_client.get_list_inventario_por_codigo(item.cuenta)
                if len(wo_inventarios.content) == 0:
                    raise HTTPException(status_code=404, detail=f'El inventario {item.cuenta} no se encontro')
                wo_producto = wo_inventarios.content[0]
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
                prefijo=14,  # 1 -> Sin Prefijo, 14 -> FC24
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

        # Al causar documento, realizar la contabilización del documento para que se apliquen los cálculos de WO
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
        return False
        # endregion log error
    except Exception as e:
        # region log error
        compra_update = compra.model_copy()
        compra_update.log = str(e) if str(e) else traceback.format_exc()
        await compra_query.update(session, compra_update, compra.id)
        return False
        # endregion log error


if __name__ == '__main__':
    from asyncio import run
    # from app.models.db.session import get_async_session

    async def main():
        invoice_json_string = '{ "body": { "id": "FE185806", "uuid": "f83aec19a46f3dd47ab5fa7b97d14fd5e05064fd0b09b741f2d9a6d195aeeb2d8ffc9c7d3c621ba29fd282d61b609c72", "fecha": "2025-10-21", "emisor": { "razonsocial": "CRISTHIAM MANUEL ULLOA ACOSTA", "nombrecomercial": "INMADEC", "telefono": "7894719", "email": "inmadec@gmail.com", "documento": "91046104", "digitoverificacion": "7", "tipodocumento": "31", "responsabilidadesfiscales": "R-99-PN", "nameresponsabilidadesfiscales": "No aplica – Otros *", "esquematributario": { "id": "01", "name": "IVA" }, "pais": "Colombia", "departamento": "Córdoba", "ciudad": "Montería", "ciudad_id": "23001", "address": "CL 44 4 18 BRR LOS LAURELES" }, "receptor": { "razonsocial": "COCO SALVAJE S.A.S.", "documento": "900912246" }, "moneda": "COP", "subtotal": "171764.69", "total": 204399.98, "descuento": 0, "impuestos": [ { "id": "01", "impuesto": "IVA", "base": "27731.10", "porcentaje": "19.00", "monto": "5268.91", "roundingamount": "0.00" }, { "id": "01", "impuesto": "IVA", "base": "33529.41", "porcentaje": "19.00", "monto": "6370.59", "roundingamount": "0.00" }, { "id": "01", "impuesto": "IVA", "base": "7563.02", "porcentaje": "19.00", "monto": "1436.97", "roundingamount": "0.00" }, { "id": "01", "impuesto": "IVA", "base": "27310.92", "porcentaje": "19.00", "monto": "5189.07", "roundingamount": "0.00" }, { "id": "01", "impuesto": "IVA", "base": "75630.24", "porcentaje": "19.00", "monto": "14369.75", "roundingamount": "0.00" } ], "lineitems": [ { "nombre": "SILICONA TRANSPARENTE TUBO 280ML UNIDAD", "cantidad": "3.00", "valorunitario": "9243.70", "total": 27731.100000000002, "unidad": "94", "cantidadbase": "3.00", "impuestos": [ { "id": "01", "impuesto": "IVA", "base": "27731.10", "porcentaje": "19.00", "monto": "5268.91", "roundingamount": "0.00" } ], "descripcion": "El vinilo adhesivo mate es una lámina de PVC autoadherible con acabado opaco, ideal para rotulación, decoración y personalización, que reduce reflejos y proyecta un estilo moderno, sobrio y profesional\\nwww.printdepot.mx\\n+1\\n .", "nombre_unidad": "Unidad", "inventario": "", "cuenta": "529595", "kg": null, "und": 3 }, { "nombre": "RECOLECTOR DE ORINA DEXCO", "cantidad": "50", "valorunitario": "847.0600", "total": 42353, "unidad": "94", "cantidadbase": "50", "impuestos": [ { "id": "01", "impuesto": "IVA", "base": "42353.0000", "porcentaje": "19.00", "monto": "8047.0700", "roundingamount": "0.00" } ], "nombre_unidad": "Unidad", "inventario": "", "cuenta": "529595", "kg": null, "und": 50 }, { "nombre": "CAJA ORGANIZADORA CON BROCHES Y RUEDAS 5", "cantidad": "5.00", "valorunitario": "60420.17", "total": 302100.85, "unidad": "WSD", "cantidadbase": "5.00", "impuestos": [ { "id": "01", "impuesto": "IVA", "base": "302100.84", "porcentaje": "19.00", "monto": "57399.16", "roundingamount": "0.00" } ], "nombre_unidad": "Unidad", "inventario": "", "cuenta": "529595", "kg": null, "und": 5 }, { "nombre": "FLETES NACIONALES", "cantidad": "1.00", "valorunitario": "12605.04", "total": 12605.04, "unidad": "WSD", "cantidadbase": "1.00", "impuestos": [ { "id": "01", "impuesto": "IVA", "base": "12605.04", "porcentaje": "19.00", "monto": "2394.96", "roundingamount": "0.00" } ], "nombre_unidad": "Unidad", "inventario": "", "cuenta": "523550", "kg": null, "und": 1 }, { "nombre": "PAPEL RESMA FOTOCOPIA MARFIL 75GR CARTA", "cantidad": "2", "valorunitario": "17000.00", "total": 34000, "unidad": "NIU", "cantidadbase": "2.00", "impuestos": [ { "id": "01", "impuesto": "IVA", "base": "28571.00", "porcentaje": "19.00", "monto": "5429.00", "roundingamount": "0.00" } ], "nombre_unidad": "Unidad", "inventario": "", "cuenta": "51953001", "kg": null, "und": 2 } ], "pago": "1", "fechapago": "2025-10-21" }, "headers": { "authorization": "**hidden**", "accept": "application/json,text/html,application/xhtml+xml,application/xml,text/*;q=0.9, image/*;q=0.8, */*;q=0.7" }, "method": "POST", "uri": "https://api.cocosalvajeapps.com/facturacion/compra", "gzip": true, "rejectUnauthorized": true, "followRedirect": true, "resolveWithFullResponse": true, "followAllRedirects": true, "timeout": 300000, "encoding": null, "json": false, "useStream": true }'
        invoice = Invoice(**json.loads(invoice_json_string)['body'])
        async for session in get_async_session():
            async with session:
                await facturar_compra_invoice(invoice, session)

    run(main())
