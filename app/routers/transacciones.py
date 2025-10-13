from enum import Enum

from fastapi import APIRouter, Depends, BackgroundTasks, status

from app.internal.integrations.shopify import ShopifyGraphQLClient
from app.internal.integrations.shopify_world_office import facturar_orden_shopify_world_office
from app.internal.log import factory_logger
from app.models.db.session import AsyncSessionDep
from app.models.db.transacciones import Pedido, PedidoCreate, PedidoLogs
from app.routers.auth import validar_access_token
from app.routers.base import CRUD
from app.internal.query.transacciones import PedidoQuery
from app.config import Environments, config


class Tags(Enum):
    TRANSACCIONES = 'Transacciones'


router = APIRouter(
    prefix='/transacciones',
    tags=[Tags.TRANSACCIONES],
    responses={404: {'description': 'No encontrado'}},
    dependencies=[Depends(validar_access_token)],
)

CRUD(router, 'pedido', PedidoQuery(), Pedido, PedidoCreate)

log_transacciones = factory_logger('transacciones')


@router.post(
    '/facturar-pendientes',
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(validar_access_token)],
)
async def facturar_pendientes(
    session: AsyncSessionDep,
    background_tasks: BackgroundTasks,
):
    pedido_query = PedidoQuery()
    pedidos = await pedido_query.get_pendientes_facturar(session)
    log_transacciones.info(
        f'Se encontraron {len(pedidos)} pedidos pendientes de facturar, {[x.numero for x in pedidos]}'
    )

    if config.environment in [Environments.DEVELOPMENT.value, Environments.STAGING.value]:
        return True

    async def task(pedidos: list[Pedido]):
        for pedido in pedidos:
            if not pedido.numero:
                continue
            if pedido.log == PedidoLogs.NO_FACTURAR.value:
                continue
            orden = await ShopifyGraphQLClient().get_order_by_number(pedido.numero)
            if orden is None:
                log_transacciones.error(f'No se encontró orden con número {pedido.numero}')
            pedido_update = pedido.model_copy()
            pedido_update.q_intentos = pedido.q_intentos - 1
            await pedido_query.update(session, pedido_update, pedido.id)
            await facturar_orden_shopify_world_office(orden)

        log_transacciones.info(f'Se intentarón facturar los pedidios: {", ".join([str(x.numero) for x in pedidos])}')

    background_tasks.add_task(task, pedidos)
    return True


@router.post(
    '/facturar/{pedido_number}',
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(validar_access_token)],
)
async def facturar_pedido(background_tasks: BackgroundTasks, pedido_number: int):
    if config.environment in [Environments.DEVELOPMENT.value, Environments.STAGING.value]:
        return True

    async def task(pedido_number: int):
        orden = await ShopifyGraphQLClient().get_order_by_number(pedido_number)
        if orden is None:
            log_transacciones.error(f'No se encontró orden con número {pedido_number}')
        await facturar_orden_shopify_world_office(orden)

    background_tasks.add_task(task, pedido_number)
    return True
