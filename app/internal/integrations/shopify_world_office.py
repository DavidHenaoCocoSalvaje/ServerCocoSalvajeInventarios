# app.internal.integrations.shopify_world_office.py


import traceback
from datetime import date, datetime, timedelta, time

import holidays_co

from app.internal.gen.utilities import DateTz, get_weekday, next_business_day, reemplazar_acentos_graves
from app.internal.integrations.addi import AddiClient
from app.internal.integrations.shopify import ShopifyGraphQLClient
from app.internal.query.transacciones import PedidoQuery
from app.models.pydantic.world_office.general import WOCiudad
from app.models.pydantic.world_office.terceros import ResponsabilidadFiscal, WODireccion, WOTercero, WOTerceroCreateEdit
from app.internal.integrations.world_office import WOException, WoClient
from app.models.db.transacciones import Pedido, PedidoCreate, PedidoLogs
from app.models.db.session import get_async_session
from app.models.pydantic.shopify.order import Order
from app.models.pydantic.world_office.facturacion import (
    WODocumentoVentaCreate,
    WODocumentoVentaTipo,
    WODocumentoVentaDetail,
    WOReglone,
)
from app.internal.log import LogLevel, factory_logger
from asyncio import sleep, TimeoutError

from sqlalchemy.ext.asyncio import AsyncSession

# Seguridad

# Facturacion
from app.config import config


log_facturacion = factory_logger('facturacion', file=True)
log_debug = factory_logger('debug', level=LogLevel.DEBUG, file=False)


def validar_identificacion(identificacion: str) -> bool:
    if not identificacion:
        return False
    # Validar una longitud entre 5 y 10 digitos para evitar facturar con documentos inválidos
    if len(identificacion) < 5 or len(identificacion) > 10:
        return False
    return True


def get_date_for_invoice(
    fecha: datetime | date,
    hora_fin_jornada_last_working_day: time = time(hour=16, minute=30),
    no_working_days: list[int] = [5, 6],
    fin_jornada_working_days: time = time(hour=17, minute=30),
):
    holidays = {h.date for h in holidays_co.get_colombia_holidays_by_year(fecha.year)}
    weekday = get_weekday(fecha)
    if weekday in no_working_days or fecha in holidays:
        return next_business_day(fecha)

    if isinstance(fecha, datetime) and fecha.time() > hora_fin_jornada_last_working_day:
        tomorrow = fecha + timedelta(days=1)
        tomorrow_weekday = get_weekday(tomorrow)
        if tomorrow in holidays or tomorrow_weekday in no_working_days:
            return next_business_day(tomorrow)

    if isinstance(fecha, datetime) and fecha.time() > fin_jornada_working_days:
        return fecha + timedelta(days=1)

    return fecha


async def get_or_create_pedido_by_number(number: int, pedido_query: PedidoQuery, session: AsyncSession) -> Pedido:
    pedido = await pedido_query.get_by_number(session, number)
    if pedido is None:
        pedido_create = PedidoCreate(numero=number)
        pedido = await pedido_query.create(session, pedido_create)
    return pedido


def get_identificacion_tercero(order: Order) -> str:
    identificacion_billing_address = order.billingAddress.identificacion
    identificacion_shipping_address = order.shippingAddress.identificacion
    identificacion_tercero = identificacion_billing_address
    if not validar_identificacion(identificacion_tercero):
        identificacion_tercero = identificacion_shipping_address
    if not validar_identificacion(identificacion_tercero):
        raise ValueError(f'Identificacion inválida: {identificacion_tercero}')
    return identificacion_tercero


async def get_wo_ciudad_from_order(wo_client: WoClient, order: Order) -> WOCiudad:
    # 1. Realizar búsqueda por nombre en dirección de facturación
    log = []
    nombre = order.billingAddress.city
    try:
        return await wo_client.buscar_ciudad(nombre=nombre)
    except WOException as e:
        log.append(str(e))
    except Exception as e:
        log.append(str(e))

    # 2 Realizar búsqueda por nombre en dirección de envío
    nombre = order.shippingAddress.city
    try:
        return await wo_client.buscar_ciudad(nombre=nombre)
    except WOException as e:
        log.append(str(e))
    except Exception as e:
        log.append(str(e))

    # 3 Realizar búsqueda por departamento en dirección de facturación
    log = []
    departamento = order.billingAddress.province
    try:
        return await wo_client.buscar_ciudad(departamento=departamento)
    except WOException as e:
        log.append(str(e))
    except Exception as e:
        log.append(str(e))

    # 4 Realizar búsqueda por departamento en dirección de envío
    departamento = order.shippingAddress.province
    try:
        return await wo_client.buscar_ciudad(departamento=departamento)
    except WOException as e:
        log.append(str(e))
    except Exception as e:
        log.append(str(e))

    msg = '\n\n'.join([str(x) for x in log])
    raise Exception(msg.strip())


async def get_valid_wo_tercero(wo_client: WoClient, order: Order, identificacion_tercero: str) -> WOTercero:
    """Busca si el tercero existe y es válido para facturar el pedido (Es cliente y tiene dirección principal).
    Si el terceo no existe, se crea.
    Si el tercero existe pero no es válido, se actualiza.
    """
    ...
    wo_tercero = await wo_client.get_tercero(identificacion_tercero)

    if (
        wo_tercero
        and wo_tercero.is_client()
        and wo_tercero.tieneDirPrincipal
        and wo_tercero.direccionPrincipal.direccion
    ):
        return wo_tercero

    wo_ciudad = await get_wo_ciudad_from_order(wo_client, order)
    ciudad_id = wo_ciudad.id
    telefono = order.billingAddress.telefono or order.shippingAddress.telefono
    email = order.email if order.email else 'sinemail@mail.com'
    # El elemento 0 en la dirección es el documento de identidad, por lo cúal se omite.
    address = (
        ', '.join(order.billingAddress.formatted[1:])
        if order.billingAddress.formatted
        else ', '.join(order.shippingAddress.formatted[1:])
    )
    names = order.billingAddress.firstName.strip() or order.shippingAddress.firstName.strip()
    names_split = names.split(' ')
    names_split_capitalized = [x.capitalize() for x in names_split]
    primer_nombre = reemplazar_acentos_graves(names_split_capitalized[0])
    segundo_nombre = reemplazar_acentos_graves(' '.join(names_split_capitalized[1:]) if len(names_split) > 1 else '')

    last_name = order.billingAddress.lastName.strip() or order.shippingAddress.lastName.strip()
    last_name_split = last_name.split(' ')
    last_name_split_capitalized = [x.capitalize() for x in last_name_split]
    primer_apellido = reemplazar_acentos_graves(last_name_split_capitalized[0])
    segundo_apellido = reemplazar_acentos_graves(
        ' '.join(last_name_split_capitalized[1:]) if len(last_name_split) > 1 else ''
    )

    """ Cuando se crea un tercero, 
    la dirección tiene un nombre, este causa error si es un mombre muy largo,
    por lo cúal hace falta especificar el nombre para evitar errores. """
    direcciones = [
        WODireccion(
            nombre='Principal',
            direccion=address,
            senPrincipal=True,
            emailPrincipal=email,
            telefonoPrincipal=telefono,
            ubicacionCiudad=WOCiudad(
                id=ciudad_id,
            ),
        )
    ]

    wo_tercero_create = WOTerceroCreateEdit(
        idTerceroTipoIdentificacion=3,  # Cédula de ciudadanía
        identificacion=identificacion_tercero,
        primerNombre=primer_nombre,
        segundoNombre=segundo_nombre,
        primerApellido=primer_apellido,
        segundoApellido=segundo_apellido,
        idCiudad=ciudad_id,
        direccion=address,
        direcciones=direcciones,
        idTerceroTipos=[4],  # Cliente
        idTerceroTipoContribuyente=6,
        idClasificacionImpuestos=1,
        telefono=telefono,
        email=email,
        plazoDias=30,
        responsabilidadFiscal=[ResponsabilidadFiscal.NO_RESPONSABLE_DE_IVA],
    )

    if wo_tercero is None:
        wo_tercero = await wo_client.crear_tercero(wo_tercero_create)
    elif not wo_tercero.is_client():
        wo_tercero_create.id = wo_tercero.id
        wo_tercero_create.idTerceroTipoIdentificacion = wo_tercero.terceroTipoIdentificacion.id
        wo_tercero_create.idTerceroTipos = wo_tercero.idTerceroTipos + [4]  # Cliente
        wo_tercero = await wo_client.editar_tercero(wo_tercero_create)

    return wo_tercero


async def get_wo_reglones_from_order(wo_client: WoClient, order: Order) -> list[WOReglone]:
    reglones: list[WOReglone] = []
    for line_intem in order.lineItems.nodes:
        inventario = await wo_client.get_inventario_por_codigo(line_intem.sku)
        impuestos = inventario.impuestos
        generator = (
            impuesto_element.valor for impuesto_element in impuestos if impuesto_element.impuesto.tipo == 'IVA'
        )
        iva = next(generator, 0)
        # World Office adiciona el IVA automáticamente, se envía el precio con IVA descontado.
        valor_unitario = line_intem.discounted_unit_price_iva_discount(iva)

        reglone = WOReglone(
            idInventario=inventario.id,
            unidadMedida='und',
            cantidad=line_intem.quantity,
            valorUnitario=valor_unitario,
            idBodega=1,
        )
        if line_intem.porc_discount > 0:
            reglone.porDescuento = line_intem.porc_discount
        reglones.append(reglone)

    costo_envio = int(order.shippingLine.originalPriceSet.shopMoney.amount)
    if costo_envio > 0:
        # El id de inventario que correspnde a FLETE en World Office es 1079
        reglones.append(
            WOReglone(idInventario='1079', unidadMedida='und', cantidad=1, valorUnitario=costo_envio, idBodega=1)
        )

    return reglones


class ShopifyWorldOffice:
    def __init__(self, shopify_client: ShopifyGraphQLClient, wo_client: WoClient):
        self.shopify = shopify_client
        self.wo = wo_client


async def facturar_orden_shopify_world_office(orden: Order, force=False):  # BackgroundTasks No lanzar excepciones.
    async for session in get_async_session():
        async with session:
            pedido_query = PedidoQuery()
            pedido = await get_or_create_pedido_by_number(orden.number, pedido_query, session)
            if pedido.factura_id:
                # Si el pedido ya se encuentra facturado se detiene el proceso.
                return
            if not pedido.id:
                return

            if not orden.fullyPaid:
                msg = f'financialStatus: {orden.displayFinancialStatus}'
                pedido_update = pedido.model_copy()
                pedido_update.log = msg
                await pedido_query.update(session, pedido_update, pedido.id)
                return
            else:
                # Se registra pago
                pedido_update = pedido.model_copy()
                pedido_update.pago = orden.fullyPaid
                await pedido_query.update(session, pedido_update, pedido.id)

            wo_client = WoClient()
            order_tags_lower = {x.strip().lower() for x in orden.tags}
            if PedidoLogs.NO_FACTURAR.value.lower() in order_tags_lower and not force:
                pedido_update = pedido.model_copy()
                pedido_update.log = PedidoLogs.NO_FACTURAR.value
                pedido_update.q_intentos = 0
                await pedido_query.update(session, pedido_update, pedido.id)
                return

            try:
                identificacion_tercero = get_identificacion_tercero(orden)
            except Exception as e:
                identificacion_tercero = None
                pedido_update = pedido.model_copy()
                pedido_update.log = f'{type(e).__name__}: {e}'
                await pedido_query.update(session, pedido_update, pedido.id)
                return

            concepto = f'{config.wo_concepto} - Pedido {orden.number}'
            factura = WODocumentoVentaDetail()
            try:
                wo_tercero = await get_valid_wo_tercero(wo_client, orden, identificacion_tercero)

                reglones = await get_wo_reglones_from_order(wo_client, orden)

                # Si los pagos son por wompi (contado), si son por addi (pse: contado, credito: credito, por defecto se deja en crédito)
                # Addi Crédito(paymetType: BNPL)
                # 4 para contado, 5 para credito
                id_forma_pago = 5 if any('credito' in tag or 'crédito' in tag for tag in order_tags_lower) else 4
                if (
                    orden.transactions
                    and len(orden.transactions) == 1
                    and orden.transactions[0].gateway == 'Addi Payment'
                ):
                    payment_id = orden.transactions[0].paymentId
                    addi_client = AddiClient()
                    await addi_client.get_access_token()
                    addi_transacions = await addi_client.get_transaccions_by_payment_id(payment_id)
                    if all(t.paymentType == 'BNPL' for t in addi_transacions.transactions):
                        id_forma_pago = 5  # Crédito
                        await ShopifyGraphQLClient().taggs_add(id=orden.id, tags=['ADDI CREDITO'])
                    else:
                        await ShopifyGraphQLClient().taggs_add(id=orden.id, tags=['ADDI PSE'])

                # if all(x.gateway == 'Addi Payment' for x in order.transactions):
                wo_documento_venta_create = WODocumentoVentaCreate(
                    fecha=get_date_for_invoice(DateTz.today()),
                    prefijo=config.wo_prefijo,  # 1 Sin prefijo, 13 FELE
                    documentoTipo=WODocumentoVentaTipo.FACTURA_VENTA,
                    concepto=concepto,
                    idEmpresa=1,  # CocoSalvaje
                    idTerceroExterno=wo_tercero.id,
                    idTerceroInterno=1,  # 1 CocoSalvaje, 1834 Lucy
                    idFormaPago=id_forma_pago,
                    idMoneda=31,
                    porcentajeDescuento=True,
                    reglones=reglones,
                )

                factura = await wo_client.crear_factura_venta(wo_documento_venta_create)
                if not factura.id or not factura.numero:
                    pedido_update = pedido.model_copy()
                    pedido_update.log = factura.model_dump_json()
                    await pedido_query.update(session, pedido_update, pedido.id)
                    return

            except TimeoutError:
                # Si no se recibe respuesta esperar 30 segundos más y validar si se creo la factura.
                await sleep(30)
                factura = await wo_client.documento_venta_por_concepto(concepto)
            except Exception as e:
                """En ocasiones world office crea la factura correctamente pero no retorna la respuesta esperada,
                se intenta consultar por el concepto para verificar que realmente no se creó la factura.
                """
                pedido_update = pedido.model_copy()
                if not str(e):
                    log_debug.debug(repr(e))
                    log_debug.debug(traceback.format_exc())
                pedido_update.log = str(e) if str(e) else 'Error desconocido'
                await pedido_query.update(session, pedido_update, pedido.id)
                return

            # Se registra número de factura antes de contabilizar.
            pedido_update = pedido.model_copy()
            pedido_update.factura_id = factura.id if factura.id else None
            pedido_update.factura_numero = factura.numero

            pedido = await pedido_query.update(session, pedido_update, pedido.id)

            if not pedido.id or not pedido.factura_id:
                return

            try:
                if not pedido.contabilizado:
                    factura = await wo_client.get_documento_venta(pedido.factura_id)
                    contabilizar = await wo_client.contabilizar_documento(
                        wo_client.Paths.Ventas.contabilizar, pedido.factura_id
                    )
                    pedido_update = pedido.model_copy()
                else:
                    return

            except TimeoutError:
                contabilizar = True
            except Exception as e:
                pedido_update = pedido.model_copy()
                pedido_update.log = str(e) if str(e) else traceback.format_exc()
                await pedido_query.update(session, pedido_update, pedido.id)
                return

            pedido_update.contabilizado = contabilizar
            pedido_update.log = None
            pedido = await pedido_query.update(session, pedido_update, pedido.id)
