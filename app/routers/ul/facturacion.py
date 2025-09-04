# app/routers/inventario.py


from app.internal.gen.utilities import DateTz
from app.models.pydantic.world_office.general import WOCiudad
from app.models.pydantic.world_office.terceros import WODireccion, WOTerceroCreate
from app.internal.integrations.world_office import WoClient
from app.models.db.transacciones import PedidoCreate
from app.models.db.session import get_async_session
from app.models.pydantic.shopify.order import Order
from app.models.pydantic.world_office.facturacion import WODocumentoVentaCreate, WOReglone
from app.internal.log import LogLevel, factory_logger

# Seguridad

# Facturacion
from app.config import config


# Base de datos (Repositorio)
from app.internal.query.transacciones import (
    pedido_query,
)

log_inventario = factory_logger('inventario', file=True)
log_inventario_shopify = factory_logger('inventario_shopify', file=True)
log_debug = factory_logger('debug', level=LogLevel.DEBUG, file=False)


async def procesar_pedido_shopify(order: Order, edit: bool = False):  # BackgroundTasks No lanzar excepciones.
    async for session in get_async_session():
        async with session:
            pedido = await pedido_query.get_by_number(session, order.number)

            # Si es un pedido que se está editando, se verifica si ya existe y si no está facturado para evitar duplicar registros
            if edit and pedido and pedido.factura_id and pedido.id:
                pedido_create = pedido.model_copy()
                pedido_create.log = 'Pedido editado, ya facturado'
                await pedido_query.update(session, pedido_create, pedido.id)
                return

            # Se registra pedido antes de crear factura por si algo sale mal tener un registro.
            if pedido is None:
                pedido_create = PedidoCreate(numero=str(order.number))
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

            wo_client = WoClient()
            identificacion_tercero = order.billingAddress.identificacion or order.shippingAddress.identificacion
            if not pedido.factura_id:
                # Cuando un cliente realiza una compra en shopify, El documento de identidad se solicita en el campo "company" en la dirección de facturación.
                if not identificacion_tercero:
                    msg = 'Falta documento de identidad'
                    pedido_update = pedido.model_copy()
                    pedido_update.log = msg
                    await pedido_query.update(session, pedido_update, pedido.id)

                    log_inventario_shopify.debug(msg)
                    return

            order_tags_lower = [x.lower().replace(' ', '_') for x in order.tags]
            for tag in order_tags_lower:
                if 'no_facturar' in tag:
                    msg = 'No facturar'
                    pedido_update = pedido.model_copy()
                    pedido_update.log = msg
                    pedido_update.q_intentos = 0
                    await pedido_query.update(session, pedido_update, pedido.id)
                    return

            try:
                factura = await facturar_orden(wo_client, order, identificacion_tercero, order_tags_lower)
            except Exception as e:
                pedido_update = pedido.model_copy()
                pedido_update.log = str(e)
                await pedido_query.update(session, pedido_update, pedido.id)
                return

            # Se registra número de factura por si pasa algo antes de contabilizar.
            pedido_update = pedido.model_copy()
            pedido_update.factura_id = str(factura.id)
            pedido_update.factura_numero = str(factura.numero)

            pedido = await pedido_query.update(session, pedido_update, pedido.id)
            if not pedido.id:
                return

            try:
                factura = await wo_client.get_documento_venta(int(pedido.factura_id))
                contabilizar = await wo_client.contabilizar_documento_venta(int(pedido.factura_id))
                if not pedido.contabilizado:
                    pedido_update = pedido.model_copy()
                    pedido_update.contabilizado = contabilizar
                    pedido = await pedido_query.update(session, pedido_update, pedido.id)

            except Exception as e:
                pedido_update = pedido.model_copy()
                pedido_update.log = str(e)
                await pedido_query.update(session, pedido_update, pedido.id)
                return

            log_debug.info(f'Pedido procesado: {order.number}, factura: {pedido.factura_numero}')


async def facturar_orden(wo_client: WoClient, order: Order, identificacion_tercero: str, tags: list[str]):
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

    names = order.billingAddress.firstName or order.shippingAddress.firstName
    names_split = names.split(' ')
    primer_nombre = names_split[0]
    segundo_nombre = ' '.join(names_split[1:]) if len(names_split) > 1 else ''

    last_name = order.billingAddress.lastName or order.shippingAddress.lastName
    last_name_split = last_name.split(' ')
    primer_apellido = last_name_split[0]
    segundo_apellido = ' '.join(last_name_split[1:]) if len(last_name_split) > 1 else ''

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

        kwargs = {}
        if line_intem.porc_discount > 0:
            kwargs['porDescuento'] = line_intem.porc_discount
        reglones.append(
            WOReglone(
                idInventario=inventario.id,
                unidadMedida='und',
                cantidad=line_intem.quantity,
                valorUnitario=valor_unitario,
                idBodega=1,
                **kwargs,
            )
        )

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
        concepto=config.wo_concepto,
        idEmpresa=1,  # CocoSalvaje
        idTerceroExterno=wo_tercero.id,
        idTerceroInterno=1,  # 1 CocoSalvaje, 1834 Lucy
        idFormaPago=id_forma_pago,
        idMoneda=31,
        reglones=reglones,
    )

    return await wo_client.crear_factura_venta(wo_documento_venta_create)
