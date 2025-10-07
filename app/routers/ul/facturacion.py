# app/routers/inventario.py


import traceback

from app.internal.gen.utilities import DateTz, reemplazar_acentos_graves
from app.internal.integrations.shopify import ShopifyGraphQLClient, ShopifyInventario
from app.internal.query.transacciones import PedidoQuery
from app.models.pydantic.world_office.general import WOCiudad
from app.models.pydantic.world_office.terceros import WODireccion, WOTerceroCreate
from app.internal.integrations.world_office import WoClient
from app.models.db.transacciones import PedidoCreate, PedidoLogs
from app.models.db.session import get_async_session
from app.models.pydantic.shopify.order import Order
from app.models.pydantic.world_office.facturacion import WODocumentoVentaCreate, WOReglone
from app.internal.log import LogLevel, factory_logger
from asyncio import sleep, TimeoutError

# Seguridad

# Facturacion
from app.config import config


log_facturacion = factory_logger('facturacion', file=True)
log_debug = factory_logger('debug', level=LogLevel.DEBUG, file=False)


async def validar_identificacion(identificacion: str) -> bool:
    if not identificacion:
        return False
    # Validar una longitud entre 5 y 10 digitos para evitar facturar con documentos inválidos
    if len(identificacion) < 5 or len(identificacion) > 10:
        return False
    return True

async def procesar_pedido_shopify(
    order_number: int | None = None, order_gid: str | None = None, f=False
):  # BackgroundTasks No lanzar excepciones.
    await sleep(30)

    shopify_graphql_client = ShopifyGraphQLClient()
    if order_gid:
        order_response = await shopify_graphql_client.get_order(order_gid)
        order = order_response.data.order
    elif order_number:
        order = await shopify_graphql_client.get_order_by_number(int(order_number))
    else:
        msg = 'No se proporciono order_gid ni pedido_number'
        log_facturacion.error(msg)
        return

    await ShopifyInventario().crear_movimientos_orden(order)

    async for session in get_async_session():
        async with session:
            pedido_query = PedidoQuery()
            pedido = await pedido_query.get_by_number(session, order.number)

            # Se registra pedido antes de crear factura por si algo sale mal tener un registro.
            if pedido is None:
                pedido_create = PedidoCreate(numero=order.number)
                pedido = await pedido_query.create(session, pedido_create)

            if not pedido.id:
                return

            if not order.fullyPaid:
                msg = f'financialStatus: {order.displayFinancialStatus}'
                pedido_update = pedido.model_copy()
                pedido_update.log = msg
                await pedido_query.update(session, pedido_update, pedido.id)
                return
            else:
                # Se registra pago
                pedido_update = pedido.model_copy()
                pedido_update.pago = order.fullyPaid
                await pedido_query.update(session, pedido_update, pedido.id)

            try:
                identificacion_billing_address = order.billingAddress.identificacion
                identificacion_shipping_address = order.shippingAddress.identificacion
                identificacion_tercero = identificacion_billing_address
                if not validar_identificacion(identificacion_tercero):
                    identificacion_tercero = identificacion_shipping_address
                
                # Cuando un cliente realiza una compra en shopify, El documento de identidad se solicita en el campo "company" en la dirección de facturación.
                if not identificacion_tercero:
                    msg = PedidoLogs.FALTA_DOCUMENTO_DE_IDENTIDAD.value
                    pedido_update = pedido.model_copy()
                    pedido_update.log = msg
                    await pedido_query.update(session, pedido_update, pedido.id)

                    log_facturacion.debug(msg)
                    return

                if not validar_identificacion(identificacion_tercero):
                    raise ValueError('Identificacion inválida')

            except Exception as e:
                identificacion_tercero = None
                pedido_update = pedido.model_copy()
                pedido_update.log = f'{type(e).__name__}: {e}'
                await pedido_query.update(session, pedido_update, pedido.id)
                return

            wo_client = WoClient()
            if not pedido.factura_id:
                order_tags_lower = [x.lower().replace(' ', '_') for x in order.tags]
                for tag in order_tags_lower:
                    if PedidoLogs.NO_FACTURAR.value.lower() in tag and not f:
                        pedido_update = pedido.model_copy()
                        pedido_update.log = PedidoLogs.NO_FACTURAR.value
                        pedido_update.q_intentos = 0
                        await pedido_query.update(session, pedido_update, pedido.id)
                        return
            
                concepto = f'{config.wo_concepto} - Pedido {order.number}'
                try:
                    factura = await facturar_orden(wo_client, order, identificacion_tercero, order_tags_lower, concepto)
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

                # Se registra número de factura por si pasa algo antes de contabilizar.
                pedido_update = pedido.model_copy()
                pedido_update.factura_id = factura.id if factura.id else None
                pedido_update.factura_numero = factura.numero

                pedido = await pedido_query.update(session, pedido_update, pedido.id)

                if not pedido.id or not pedido.factura_id:
                    return

            try:
                if not pedido.contabilizado:
                    factura = await wo_client.get_documento_venta(pedido.factura_id)
                    contabilizar = await wo_client.contabilizar_documento_venta(pedido.factura_id)
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


async def facturar_orden(
    wo_client: WoClient, order: Order, identificacion_tercero: str, tags: list[str], concepto: str
):
    # Cuando un cliente realiza una compra en shopify, El documento de identidad se solicita en el campo "company" en la dirección de facturación.
    ciudad = order.billingAddress.city or order.shippingAddress.city
    departamento = order.billingAddress.province or order.shippingAddress.province
    telefono = order.billingAddress.telefono or order.shippingAddress.telefono
    email = order.email if order.email else 'sinemail@mail.com'
    wo_ciudad = await wo_client.buscar_ciudad(departamento, ciudad)
    ciudad_id = wo_ciudad.id

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
    segundo_apellido = reemplazar_acentos_graves(' '.join(last_name_split_capitalized[1:]) if len(last_name_split) > 1 else '')

    wo_tercero = await wo_client.get_tercero(identificacion_tercero)

    """ Cuando se crea un tercero, 
    la dirección tienen un nombre, este causa error si es un mombre muy largo,
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

    if wo_tercero is None:
        tercero_create = WOTerceroCreate(
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
            responsabilidadFiscal=[7],
        )
        wo_tercero = await wo_client.crear_tercero(tercero_create)

    if not wo_tercero.is_client() and wo_tercero.tieneDirPrincipal and wo_tercero.direccionPrincipal.direccion:
        id_tercero_tipos = wo_tercero.idTerceroTipos
        id_tercero_tipos.append(4)  # Cliente
        tercero_create = WOTerceroCreate(
            id=wo_tercero.id,
            idTerceroTipoIdentificacion=wo_tercero.terceroTipoIdentificacion.id,
            identificacion=identificacion_tercero,
            primerNombre=primer_nombre,
            segundoNombre=segundo_nombre,
            primerApellido=primer_apellido,
            segundoApellido=segundo_apellido,
            idCiudad=ciudad_id,
            direccion=address,
            direcciones=direcciones,
            idTerceroTipos=id_tercero_tipos,  # Cliente
            idTerceroTipoContribuyente=6,
            idClasificacionImpuestos=1,
            telefono=telefono,
            email=email,
            plazoDias=30,
            responsabilidadFiscal=[7],
        )
        wo_tercero = await wo_client.editar_tercero(tercero_create)

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
            WOReglone(idInventario=1079, unidadMedida='und', cantidad=1, valorUnitario=costo_envio, idBodega=1)
        )

    # Si los pagos son por wompi (contado), si son por addi (pse: contado, credito: credito, por defecto se deja en crédito)
    # 4 para contado, 5 para credito
    id_forma_pago = 4
    for tag in tags:
        if 'credito' in tag:
            id_forma_pago = 5
            break

    # if all(x.gateway == 'Addi Payment' for x in order.transactions):
    wo_documento_venta_create = WODocumentoVentaCreate(
        fecha=DateTz.today(),
        prefijo=config.wo_prefijo,  # 1 Sin prefijo, 13 FEFE
        documentoTipo='FV',
        concepto=concepto,
        idEmpresa=1,  # CocoSalvaje
        idTerceroExterno=wo_tercero.id,
        idTerceroInterno=1,  # 1 CocoSalvaje, 1834 Lucy
        idFormaPago=id_forma_pago,
        idMoneda=31,
        porcentajeDescuento=True,
        reglones=reglones,
    )

    return await wo_client.crear_factura_venta(wo_documento_venta_create)
