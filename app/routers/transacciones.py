from enum import Enum

from fastapi import APIRouter, Depends, BackgroundTasks, status

from app.internal.log import factory_logger
from app.models.db.session import AsyncSessionDep
from app.models.db.transacciones import Pedido
from app.routers.auth import validar_access_token
from app.routers.base import CRUD
from app.internal.query.transacciones import pedido_query
from app.internal.integrations.shopify import ShopifyGraphQLClient
from app.routers.ul.facturacion import procesar_pedido_shopify


class Tags(Enum):
    TRANSACCIONES = 'Transacciones'


router = APIRouter(
    prefix='/transacciones',
    tags=[Tags.TRANSACCIONES],
    responses={404: {'description': 'No encontrado'}},
    dependencies=[Depends(validar_access_token)],
)

CRUD[Pedido](
    router,
    pedido_query,
    'pedido',
)

log_transacciones = factory_logger('transacciones', file=True)


@router.post(
    '/facturar_pendientes',
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(validar_access_token)],
)
async def facturar_pendientes(
    session: AsyncSessionDep,
    background_tasks: BackgroundTasks,
):
    """Se facturan los pedidos que no tienen factura y no tienen q_intentos > 0."""
    pedidos = await pedido_query.get_no_facturados(session)
    for pedido in pedidos:
        pedido_update = pedido.model_copy()
        pedido_update.q_intentos = pedido.q_intentos - 1

        if not pedido.id:
            break

        await pedido_query.update(session, pedido_update, pedido.id)

    background_tasks.add_task(task_facturar_pendientes, pedidos)
    return True


async def task_facturar_pendientes(pedidos: list[Pedido]):
    shopify_graphql_client = ShopifyGraphQLClient()
    for pedido in pedidos:
        orders_response = await shopify_graphql_client.get_order_by_number(int(pedido.numero))
        order = orders_response.data.orders.nodes[0]
        await procesar_pedido_shopify(order)
    log_transacciones.info(f'Se intentaron facturar los pedidos: {", ".join([str(x.numero) for x in pedidos])}')
