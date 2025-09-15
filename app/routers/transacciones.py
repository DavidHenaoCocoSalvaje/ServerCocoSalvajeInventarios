from enum import Enum

from fastapi import APIRouter, Depends, BackgroundTasks, status

from app.internal.log import factory_logger
from app.models.db.session import AsyncSessionDep
from app.models.db.transacciones import Pedido, PedidoCreate, PedidoLogs
from app.routers.auth import validar_access_token
from app.routers.base import CRUD
from app.internal.query.transacciones import PedidoQuery
from app.routers.ul.facturacion import procesar_pedido_shopify
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

log_transacciones = factory_logger('transacciones', file=True)


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
    for pedido in pedidos:
        pedido_update = pedido.model_copy()
        pedido_update.q_intentos = pedido.q_intentos - 1

        if not pedido.id:
            break

        await pedido_query.update(session, pedido_update, pedido.id)

    if config.environment in [Environments.DEVELOPMENT.value, Environments.STAGING.value]:
        return True

    background_tasks.add_task(task_facturar_pendientes, pedidos)
    return True


async def task_facturar_pendientes(pedidos: list[Pedido]):
    for pedido in pedidos:
        if not pedido.numero:
            continue
        if pedido.log == PedidoLogs.NO_FACTURAR.value:
            continue
        await procesar_pedido_shopify(order_number=pedido.numero)
    log_transacciones.info(f'Se intentaron facturar los pedidos: {", ".join([str(x.numero) for x in pedidos])}')
