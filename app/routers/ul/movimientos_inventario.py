if __name__ == '__main__':
    from os.path import abspath
    from sys import path as sys_path

    sys_path.append(abspath('.'))

from datetime import date
from app.internal.integrations.shopify import ShopifyGraphQLClient
from app.internal.query.inventario import MovimientoQuery
from app.models.db.session import get_async_session


async def sincronizar_movimientos_por_fehca(start: date, end: date):
    shopify_client = ShopifyGraphQLClient()
    ordenes = await shopify_client.get_orders_by_range(start, end, 20)

    order_numbers = {str(order.number) for order in ordenes.data.orders.nodes}
    order_numbers_db = []

    async for session in get_async_session():
        async with session:
            movimiento_query = MovimientoQuery()
            movimientos = await movimiento_query.get_by_soporte_ids(session, 2, list(order_numbers))
            order_numbers_db = {movimiento.soporte_id for movimiento in movimientos if movimiento.soporte_id}

    order_numbers_db = set(order_numbers_db)
    order_numbers = set(order_numbers)
    order_numbers_dif = order_numbers - order_numbers_db

    print(order_numbers_dif)


if __name__ == '__main__':
    import asyncio

    asyncio.run(sincronizar_movimientos_por_fehca(date(2025, 1, 1), date(2025, 6, 30)))
