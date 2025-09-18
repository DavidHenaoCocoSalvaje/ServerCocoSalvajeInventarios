# if __name__ == '__main__':
#     from os.path import abspath
#     from sys import path as sys_path

#     sys_path.append(abspath('.'))

# from datetime import date
# from app.internal.integrations.shopify import ShopifyGraphQLClient
# from app.internal.query.inventario import MovimientoQuery, VarianteElementoQuery
# from app.models.db.inventario import Movimiento
# from app.models.db.session import get_async_session


# async def sincronizar_movimientos_por_fechas(start: date, end: date):
#     shopify_client = ShopifyGraphQLClient()
#     orders_response = await shopify_client.get_orders_by_range(start, end, 50)

#     order_numbers = {str(order.number) for order in orders_response.data.orders.nodes}
#     order_numbers_db = []

#     async for session in get_async_session():
#         async with session:
#             movimiento_query = MovimientoQuery()
#             variante_query = VarianteElementoQuery()

#             movimientos = await movimiento_query.get_by_soporte_ids(session, 2, list(order_numbers))
#             order_numbers_db = {movimiento.soporte_id for movimiento in movimientos if movimiento.soporte_id}

#             order_numbers_db = set(order_numbers_db)
#             order_numbers = set(order_numbers)
#             order_numbers_dif = order_numbers - order_numbers_db

#             filtred_orders = [order for order in orders_response.data.orders.nodes if order.number in order_numbers_dif]
#             await shopify_client.get_orders_line_items(filtred_orders, 20)

#             for order in filtred_orders:
#                 variante_ids = [line_item.variant.legacyResourceId for line_item in order.lineItems.nodes]
#                 movimientos = [
#                     Movimiento(
#                         tipo_movimiento_id=4,  # Salida
#                         tipo_soporte_id=2,  # Pedido
#                         variante_id=line_item.variant.legacyResourceId,
#                         cantidad=line_item.quantity,
#                         bodega_id=
#                     )
#                     for line_item in order.lineItems.nodes
#                 ]


# if __name__ == '__main__':
#     import asyncio

#     asyncio.run(sincronizar_movimientos_por_fechas(date(2025, 1, 1), date(2025, 3, 31)))
