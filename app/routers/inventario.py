# app/routers/inventario.py
from enum import Enum
from fastapi import APIRouter, Depends, HTTPException, Request, status
import re


from app.internal.integrations.shopify import QueryShopify, get_inventory_info, persistir_inventory_info
from app.models.pydantic.world_office.terceros import WOTerceroCreate
from app.internal.integrations.world_office import WOException, WoClient
from app.models.db.transacciones import Pedido, PedidoCreate
from app.models.db.session import AsyncSessionDep
from app.models.pydantic.shopify.order import Order, OrderResponse, OrderWebHook
from app.models.pydantic.world_office.facturacion import WODocumentoVentaCreate, WOReglone
from app.routers.base import CRUD
from app.internal.log import LogLevel, factory_logger

# Seguridad
from app.routers.auth import hmac_validation_shopify


from app.models.db.inventario import (
    Bodega,
    Elemento,
    VarianteElemento,
    ComponentesPorVariante,
    Grupo,
    TipoMovimiento,
    TipoPrecio,
    TiposMedida,
    MedidasPorVariante,
    PreciosPorVariante,
    Movimiento,
    EstadoVariante,
    Medida,
)

# Base de datos (Repositorio)
from app.internal.query.inventario import (
    bodega_query,
    grupo_query,
    elemento_query,
    variante_elemento_query,
    componentes_por_variante_query,
    unidad_medida_query,
    precio_variante_query,
    tipo_precio_query,
    tipo_medida_query,
    medidas_por_variante_query,
    movimiento_query,
    tipo_movimiento_query,
    estado_elemento_query,
)
from app.internal.query.transacciones import (
    pedido_query,
)
from .auth import validar_access_token

log_inventario = factory_logger('inventario', file=True)
log_inventario_shopify = factory_logger('inventario_shopify', file=True)
log_debug = factory_logger('debug', level=LogLevel.DEBUG, file=False)


class Tags(Enum):
    INVENTARIO = 'Inventario'
    SHOPIFY = 'Shopify'


router = APIRouter(
    prefix='/inventario',
    tags=[Tags.INVENTARIO],
    responses={404: {'description': 'No encontrado'}},
    dependencies=[Depends(validar_access_token)],
)

shopify_router = APIRouter(
    prefix='/inventario/shopify',
    tags=[Tags.INVENTARIO, Tags.SHOPIFY],
    responses={404: {'description': 'No encontrado'}},
)


# Llamadas a la función genérica para cada modelo de inventario
CRUD[Elemento](
    router,
    elemento_query,
    'elemento',
)
CRUD[VarianteElemento](
    router,
    variante_elemento_query,
    'variante',
)
CRUD[ComponentesPorVariante](
    router,
    componentes_por_variante_query,
    'componente',
)
CRUD[Bodega](
    router,
    bodega_query,
    'bodega',
)
CRUD[Grupo](
    router,
    grupo_query,
    'grupo',
)
CRUD[Medida](
    router,
    unidad_medida_query,
    'unidad_medida',
)
CRUD[PreciosPorVariante](
    router,
    precio_variante_query,
    'precio',
)
CRUD[TipoPrecio](
    router,
    tipo_precio_query,
    'tipo_precio',
)
CRUD[TiposMedida](
    router,
    tipo_medida_query,
    'tipo_medida',
)
CRUD[MedidasPorVariante](
    router,
    medidas_por_variante_query,
    'medida',
)
CRUD[Movimiento](
    router,
    movimiento_query,
    'movimiento',
)
CRUD[TipoMovimiento](
    router,
    tipo_movimiento_query,
    'tipo_movimiento',
)
CRUD[EstadoVariante](
    router,
    estado_elemento_query,
    'estado',
)


# Sincronización
@shopify_router.post(
    '/sync_shopify',
    response_model=bool,
    summary='Sincroniza inventarios de Shopify con base de datos',
    description='Se registran movimiento de cargue.',
    status_code=status.HTTP_200_OK,
    tags=[Tags.INVENTARIO, Tags.SHOPIFY],
    dependencies=[Depends(validar_access_token)],
)
async def sync_shopify():
    """Sincroniza los datos de inventario desde Shopify."""
    try:
        inventory_info = await get_inventory_info()
        await persistir_inventory_info(inventory_info)
        log_inventario_shopify.debug('Inventarios de Shopify sincronizado con éxito')
        return True
    except Exception as e:
        log_inventario_shopify.error(f'Error al sincronizar inventarios de Shopify: {e}')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Pedidos
@shopify_router.post(
    '/pedido',
    status_code=status.HTTP_200_OK,
    tags=[Tags.INVENTARIO, Tags.SHOPIFY],
    dependencies=[Depends(hmac_validation_shopify)],
)
async def procesar_pedido_shopify(request: Request, session: AsyncSessionDep):
    try:
        query_shopify = QueryShopify()
        # Obtener datos de pedido
        webhook_data = await request.json()
        order_webhook = OrderWebHook(**webhook_data)
        # Se consulta la orden porque la ingormación que viene del webhook no incluye la información de la transacción.
        order_json = await query_shopify.get_order(order_webhook.admin_graphql_api_id)
        order_response = OrderResponse(**order_json)
        if not order_response.valid():
            log_inventario_shopify.error(f'Order void: {order_response.model_dump_json()}')
            return

        # Registrar pedido
        pedido_create = PedidoCreate(numero=str(order_response.data.order.number))
        pedido = await pedido_query.create(session, pedido_create)

        log_inventario_shopify.info(f'\nPedido recibido: {order_response.model_dump_json()}')
        if order_response.data.order is None:
            log_inventario_shopify.error(f'Order not found: {order_response.model_dump_json()}')
        order = order_response.data.order
        factura = await facturar_orden(order)

        # Registrar número de factura
        pedido_update = pedido.model_copy()
        pedido_update.factura = str(factura.id)
        pedido_update.factura_numero = str(factura.numero)
        pedido = await pedido_query.update(session, pedido, pedido_update)

        # Contabilizar pedido
        contabilizar = await contabilizar_pedido(pedido)
        # Registrar estado contabilización
        pedido_update = pedido.model_copy()
        pedido_update.contabilizado = contabilizar
        pedido = await pedido_query.update(session, pedido, pedido_update)

    except WOException as e:
        log_inventario_shopify.error(f'{e}')


async def facturar_orden(order: Order):
    # Si los pagos son por wompi (contado), si son por addi (pse: contado, credito: credito, por defecto se deja en crédito)
    # 4 para contado, 5 para credito
    id_forma_pago = 4
    # if all(x.gateway == 'Addi Payment' for x in order.transactions):

    # Cuando un cliente realiza una compra en shopify, El documento de identidad se solicita en el campo "company" en la dirección de facturación.
    wo_client = WoClient()
    identificacion = order.billingAddress.company or order.shippingAddress.company
    # Eliminar digíto de verificación si company contiene '-'
    if '-' in identificacion:
        identificacion = identificacion.split('-')[0]
    # La identificación puede contener carácteres no válidos, ya que en Shopify no hay validación de tipos.
    identificacion = re.sub(r'[^0-9]', '', identificacion)

    ciudad = order.billingAddress.city or order.shippingAddress.city
    departamento = order.billingAddress.province or order.shippingAddress.province
    wo_ciudad = await wo_client.buscar_ciudad(departamento, ciudad)
    ciudad_id = wo_ciudad.id

    # El elemento 0 en la dirección es el documento de identidad, por lo cúal se omite.
    address = (
        ', '.join(order.billingAddress.formatted[1:])
        if order.billingAddress.formatted
        else ', '.join(order.shippingAddress.formatted[1:])
    )

    first_name = order.billingAddress.firstName or order.shippingAddress.firstName
    primer_nombre = first_name.split(' ')[0]
    segundo_nombre = first_name.split(' ')[1] if len(first_name.split(' ')) > 1 else ''

    last_name = order.billingAddress.lastName or order.shippingAddress.lastName
    primer_apellido = last_name.split(' ')[0]
    segundo_apellido = last_name.split(' ')[1] if len(last_name.split(' ')) > 1 else ''

    wo_tercero = await wo_client.get_tercero(identificacion)

    if wo_tercero is None:
        tercero_create = WOTerceroCreate(
            idTerceroTipoIdentificacion=3,  # Cédula de ciudadanía
            identificacion=order.billingAddress.company,
            primerNombre=primer_nombre,
            segundoNombre=segundo_nombre,
            primerApellido=primer_apellido,
            segundoApellido=segundo_apellido,
            idCiudad=ciudad_id,
            direccion=address,
            idTerceroTipos=[4],  # Cliente
        )
        wo_tercero = await wo_client.crear_tercero(tercero_create)

    if not wo_tercero.is_client():
        id_tercero_tipos = wo_tercero.idTerceroTipos
        id_tercero_tipos.append(4)  # Cliente
        tercero_create = WOTerceroCreate(
            id=wo_tercero.id,
            idTerceroTipoIdentificacion=wo_tercero.terceroTipoIdentificacion.id,  # Cédula de ciudadanía
            identificacion=wo_tercero.identificacion,
            primerNombre=wo_tercero.primerNombre,
            segundoNombre=wo_tercero.segundoNombre,
            primerApellido=wo_tercero.primerApellido,
            segundoApellido=wo_tercero.segundoApellido,
            idCiudad=wo_tercero.ciudad.id,
            idTerceroTipos=id_tercero_tipos,  # Cliente
        )
        wo_tercero = await wo_client.editar_tercero(tercero_create)

    reglones: list[WOReglone] = []
    for line_intem in order.lineItems.nodes:
        amount = line_intem.originalUnitPriceSet.shopMoney.amount.split('.')[0]
        reglones.append(
            WOReglone(
                idInventario=int(line_intem.sku),
                unidadMedida='und',
                cantidad=line_intem.quantity,
                valorUnitario=int(amount),
                idBodega=1,
            )
        )

    wo_documento_venta_create = WODocumentoVentaCreate(
        prefijo=1,  # Sin prefijo
        documentoTipo='FV',
        concepto='Prueba API',
        idEmpresa=1,  # CocoSalvaje
        idTerceroExterno=wo_tercero.id,
        idTerceroInterno=1,
        idFormaPago=id_forma_pago,
        idMoneda=31,
        reglones=reglones,
    )

    return await wo_client.crear_factura_venta(wo_documento_venta_create)


async def contabilizar_pedido(pedido: Pedido):
    wo_client = WoClient()
    return await wo_client.contabilizar_documento_venta(int(pedido.factura_id))
