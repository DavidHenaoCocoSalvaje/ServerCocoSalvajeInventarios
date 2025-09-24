from datetime import date, datetime, timedelta
import traceback
from pydantic import BaseModel, ValidationError
from re import findall
from asyncio import gather, sleep


if __name__ == '__main__':
    from os.path import abspath
    from sys import path as sys_path

    sys_path.append(abspath('.'))

from app.internal.gen.utilities import DateTz, divide
from app.internal.query.inventario import (
    BodegaQuery,
    ElementoQuery,
    EstadoVarianteQuery,
    MovimientoQuery,
    PrecioPorVarianteQuery,
    TipoMovimientoQuery,
    TipoSoporteQuery,
    VarianteElementoQuery,
)

from app.internal.log import factory_logger, LogLevel
from app.models.pydantic.shopify.order import Order, OrderResponse, OrdersResponse
from app.internal.integrations.base import BaseClient, ClientException
from app.models.db.inventario import (
    Bodega,
    BodegaCreate,
    Elemento,
    ElementoCreate,
    Movimiento,
    MovimientoCreate,
    PreciosPorVariante,
    PreciosPorVarianteCreate,
    VarianteElemento,
    VarianteElementoCreate,
)
from app.models.db.session import get_async_session
from app.models.pydantic.shopify.inventario import (
    InventoryLevelsResponse,
    Location,
    Product,
    ProductsResponse,
    Variant,
    VariantsResponse,
)

from app.config import config

log_shopify = factory_logger('shopify', file=True)
log_debug = factory_logger('debug', level=LogLevel.DEBUG, file=False)


class ShopifyException(ClientException):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ShopifyGraphQLClient(BaseClient):
    __instance = None
    __currently_available: int

    class Variables(BaseModel):
        num_items: int = 10
        cursor: str | None = None
        search_query: str | None = None
        id: int | None = None
        gid: str | None = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(ShopifyGraphQLClient, cls).__new__(cls)
        return cls.__instance

    def __init__(
        self,
        shop: str = config.shop_shopify,
        version: str = config.shop_version,
        access_token: str = config.api_key_shopify,
    ):
        super().__init__(min_interval=0)
        self.host = f'https://{shop}.myshopify.com/admin/api/{version}/graphql.json'
        self.access_token = access_token
        self.headers = {
            'Content-Type': 'application/json',
            'X-Shopify-Access-Token': access_token,
        }
        self.payload = {}
        self.response = {}

    async def _execute_query(self, query: str, **variables) -> dict:
        self.payload = {'query': query, 'variables': variables or {}}
        self.response = {}

        try:
            self.response = await self.request('POST', self.headers, self.host, payload=self.payload)
            self.__currently_available = self.response['extensions']['cost']['throttleStatus']['currentlyAvailable']
            max_available = self.response['extensions']['cost']['throttleStatus']['maximumAvailable']
            restore_rate = self.response['extensions']['cost']['throttleStatus']['restoreRate']
            diff_available = max_available - self.__currently_available
            if self.__currently_available < 100:
                await sleep(divide(diff_available, restore_rate))
            return self.response
        except Exception as e:
            exception = ShopifyException(url=self.host, payload=self.payload, msg=type(e).__name__)
            log_shopify.error(f'Error al ejecutar consulta GraphQL: {exception} {traceback.format_exc()}')
            raise exception

    def get_specific_obj_response(self, response: dict, keys: list[str], sub_keys: list[str]):
        obj = response
        sub_objs = {}
        if not response:
            msg = 'Respuesta vacía'
            exception = ShopifyException(payload=self.payload, response=response, msg=msg)
            log_shopify.error(str(exception))
            raise exception

        for key in keys:
            obj = obj.get(key, None)

            if isinstance(obj, list):
                obj = obj[0]

            if not obj:
                msg = f'No se pudo obtener {key}, keys: {keys}, sub_keys: {sub_keys}'
                exception = ShopifyException(payload=self.payload, response=response, msg=msg)
                log_shopify.error(str(exception))
                raise exception

        for sub_key in sub_keys:
            sub_obj = obj.get(sub_key, None)
            if not sub_obj:
                exception = ShopifyException(payload=self.payload, response=response)
                log_shopify.error(f'No se pudo obtener {sub_key} de la respuesta {exception}')
                raise exception
            sub_objs[sub_key] = sub_obj

        return {'root': obj, 'sub_keys': sub_objs}

    def pagination_verify_query(self, query: str, variables: dict):
        pattern_num_items = r'\$num_items:\s*Int!'
        pattern_cursor = r'\$cursor:\s*String'
        num_items_matches = findall(pattern_num_items, query)
        cursor_matches = findall(pattern_cursor, query)
        if not len(num_items_matches) == 1 or not len(cursor_matches) == 1:
            msg = f'Query inválida, no contiene $num_items: Int! y $cursor: String una única vez\n{query}'
            exception = ShopifyException(msg=msg)
            log_shopify.error(str(exception))
            raise exception

        pattern_first = r'first:\s*\$num_items'
        pattern_after = r'after:\s*\$cursor'
        first_matches = findall(pattern_first, query)
        after_matches = findall(pattern_after, query)
        if not len(first_matches) == 1 or not len(after_matches) == 1:
            msg = f'Query inválida, no contiene first: $num_items y after: $cursor una única vez\n{query}'
            exception = ShopifyException(msg=msg)
            log_shopify.error(str(exception))
            raise exception

        if not variables.get('num_items'):
            msg = f'Variables inválidas, no contienen num_items\n{variables}'
            exception = ShopifyException(msg=msg)
            log_shopify.error(str(exception))
            raise exception

    async def _get_all(
        self,
        query: str,
        keys: list[str],
        variables: dict,
    ) -> dict:
        """
        :param keys: Lista de claves para acceder a los nodos y page_info de la respuesta
        """

        self.pagination_verify_query(query, variables)

        query_result = await self._execute_query(query, **variables)
        result = query_result
        specific_obj_response = self.get_specific_obj_response(query_result, keys, ['pageInfo', 'nodes'])

        page_info = specific_obj_response['sub_keys']['pageInfo']
        nodes = specific_obj_response['sub_keys']['nodes']
        has_next_page = page_info.get('hasNextPage', False)
        cursor = page_info.get('endCursor', None)

        while has_next_page:
            variables['cursor'] = cursor
            next_query_result = await self._execute_query(query, **variables)
            specific_obj_response = self.get_specific_obj_response(next_query_result, keys, ['pageInfo', 'nodes'])

            nodes.extend(specific_obj_response['sub_keys']['nodes'])

            page_info = specific_obj_response['sub_keys']['pageInfo']
            has_next_page = page_info.get('hasNextPage', False)
            cursor = page_info.get('endCursor', None)

        return result

    async def _get_products_base(self) -> ProductsResponse:
        query = """
            query GetProducts($num_items: Int!, $cursor: String) {
                products(first: $num_items, after: $cursor, query: "has_variant_with_components:false") {
                    nodes {
                        legacyResourceId
                        title
                    }
                    pageInfo {
                        hasNextPage
                        endCursor
                    }
                }
            }
        """
        variables = self.Variables().model_dump(exclude_none=True)
        products_json = await self._get_all(query, ['data', 'products'], variables)
        products_response = ProductsResponse(**products_json)
        return products_response

    async def get_product_by_variant_id(self, variant_id: int) -> Product:
        query = """
            query GetProductByVariantId($search_query: String!) {
                products(first: 1, query: $search_query) {
                    nodes {
                        legacyResourceId
                        title
                    }
                }
            }
        """
        variables = self.Variables(search_query=f'variant_id:{variant_id}').model_dump(exclude_none=True)
        product_json = await self._execute_query(query, **variables)
        product_response = ProductsResponse(**product_json)
        return product_response.data.products.nodes[0]

    async def get_variants_by_product_id(self, product_id: int):
        query = """
            query GetVariants($num_items: Int!, $search_query: String!, $cursor: String) {
                productVariants(first: $num_items, after: $cursor, query: $search_query) {
                    nodes {
                        product {
                            legacyResourceId
                        }
                        legacyResourceId
                        inventoryQuantity
                        title
                        price
                        inventoryItem {
                            legacyResourceId
                        }
                    }
                    pageInfo {
                        hasNextPage
                        endCursor
                    }
                }
            }
        """
        variables = self.Variables(search_query=f'product_id:{product_id}').model_dump(exclude_none=True)
        variants_json = await self._get_all(query, ['data', 'productVariants'], variables)
        variants_response = VariantsResponse(**variants_json)
        return variants_response

    async def get_product_variants(self, product: Product):
        product_variants = await self.get_variants_by_product_id(product.legacyResourceId)
        product.variants = product_variants.data.productVariants.nodes

    async def get_inventory_levels(self, inventory_item_id: int):
        query = """
            query GetInventoryLevels($num_items: Int!, $search_query: String!, $cursor: String) {
                inventoryItems(first: 1, query: $search_query) {
                    nodes {
                        sku
                        inventoryLevels(first:$num_items, after: $cursor) {
                            nodes {
                                item {
                                    variant {
                                        legacyResourceId
                                    }
                                }
                                quantities(names: ["on_hand"]) {
                                    quantity
                                }
                                location {
                                    legacyResourceId
                                    address {
                                        city
                                        province
                                        country
                                        address1
                                        formatted
                                    }
                                }
                            }
                            pageInfo {
                                hasNextPage
                                endCursor
                            }
                        }
                    }
                }
            }
        """
        variables = self.Variables(search_query=f'id:{inventory_item_id}').model_dump(exclude_none=True)
        inventory_levels_json = await self._execute_query(query, **variables)
        return InventoryLevelsResponse(**inventory_levels_json)

    async def get_variant_inventory_levels(self, variant: Variant):
        intentory_levels_response = await self.get_inventory_levels(variant.inventoryItem.legacyResourceId)
        if intentory_levels_response.data.inventoryItems.nodes:
            inventory_item = intentory_levels_response.data.inventoryItems.nodes[0]
            variant.sku = inventory_item.sku
            variant.inventoryItem.inventoryLevels.nodes = inventory_item.inventoryLevels.nodes

    async def get_porduct_variant_inventory_levels(self, product: Product, batch_size: int = 5):
        await self.get_product_variants(product)
        for i in range(0, len(product.variants), batch_size):
            batch = product.variants[i : i + batch_size]
            tasks = [self.get_variant_inventory_levels(variant) for variant in batch]
            await gather(*tasks)

    async def get_order_line_items(self, order: Order, num_items: int = 50):
        query = """
        query GetLineItemsOrder($gid: ID!, $num_items: Int!, $cursor: String) {
            order(id: $gid) {
                id
                lineItems(first:$num_items, after: $cursor) {
                    nodes {
                        name
                        quantity
                        sku
                        variant {
                            legacyResourceId
                            compareAtPrice
                        }
                        originalUnitPriceSet {
                            shopMoney {
                                amount
                                currencyCode
                            }
                        }
                        discountedUnitPriceAfterAllDiscountsSet {
                            shopMoney {
                                amount
                                currencyCode
                            }
                        }
                    }
                    pageInfo {
                        endCursor
                        hasNextPage
                    }
                }
            }
        }
        """
        variables = self.Variables(num_items=num_items, gid=order.id).model_dump(exclude_none=True)
        order_line_items_json = await self._execute_query(query, **variables)
        order.lineItems = order_line_items_json['data']['order']['lineItems']

    async def get_orders_line_items(self, orders: list[Order], batch_size=10) -> None:
        # Procesar por lotes de con asyncio.gather
        if len(orders) > 0:
            for i in range(0, len(orders), batch_size):
                batch = orders[i : i + batch_size]
                tasks = [self.get_order_line_items(order) for order in batch if batch]
                await gather(*tasks)

    async def get_orders_by_range(self, start: date, end: date, num_items: int = 20) -> list[Order]:
        start_str = DateTz.local(datetime(start.year, start.month, start.day)).utc.to_isostring
        end_str = DateTz.local(datetime(end.year, end.month, end.day)).utc.to_isostring
        query = """
            query GetOrderByRange($num_items: Int!, $search_query: String!, $cursor: String) {
                orders(first: $num_items, query: $search_query, after: $cursor) {
                    nodes {
                        id
                        fulfillments(first: 1) {
                            location {
                                legacyResourceId
                            }
                        }
                        number
                        createdAt
                        tags
                        app {
                            name
                        }
                    }
                    pageInfo {
                        endCursor
                        hasNextPage
                    }
                }
            }
        """
        # "search_query": "tofinancial_status:paid created_at:>=2025-08-01 and created_at:>=2025-08-31",
        variables = self.Variables(
            num_items=num_items, search_query=f'financial_status:paid created_at:>={start_str} created_at:<={end_str}'
        ).model_dump(exclude_none=True)
        orders_json = await self._get_all(query, ['data', 'orders'], variables)
        orders_response = OrdersResponse(**orders_json)
        await self.get_orders_line_items(orders_response.data.orders.nodes)

        return orders_response.data.orders.nodes

    async def get_order(self, order_gid: str) -> OrderResponse:
        query = """
        query GetOrder($gid: ID!) {
            order(id: $gid) {
                id
                fulfillments(first: 1) {
                    location {
                        legacyResourceId
                    }
                }
                fullyPaid
                displayFinancialStatus
                tags
                email
                number
                createdAt
                app {
                    name
                }
                customer {
                    firstName
                    lastName
                    id
                }
                transactions {
                    gateway
                    paymentId
                },
                shippingAddress {
                    firstName
                    lastName
                    company
                    address1
                    address2
                    province
                    city
                    country
                    phone
                    zip
                    formatted
                }
                billingAddress {
                    firstName
                    lastName
                    company
                    address1
                    address2
                    province
                    country
                    city
                    phone
                    zip
                    formatted
                }
                shippingLine {
                    originalPriceSet {
                        shopMoney {
                            amount
                            currencyCode
                        }
                    }
                }
            }
        }
        """
        variables = self.Variables(gid=order_gid).model_dump(exclude_none=True)
        order_json = await self._execute_query(query, **variables)
        try:
            order_response = OrderResponse(**order_json)
            await self.get_order_line_items(order_response.data.order)
        except ValidationError as e:
            msg = f'{type(e)} {OrderResponse.__name__}'
            msg += f'\n{repr(e.errors())}'
            exception = ShopifyException(url=self.host, payload=self.payload, response=order_json, msg=msg)
            raise exception
        except KeyError:
            msg = 'KeyError'
            exception = ShopifyException(url=self.host, payload=self.payload, response=order_json, msg=msg)
            raise exception

        if not order_response.valid():
            msg = 'No se obtuvo orden'
            exception = ShopifyException(url=self.host, payload=self.payload, response=order_json, msg=msg)
            raise exception

        return order_response

    async def get_order_by_number(self, order_number: int) -> Order:
        query = """
        query GetOrderByNumber($search_query: String!) {
            orders(first: 1, query: $search_query) {
                nodes {
                    id
                    fulfillments(first: 1) {
                        location {
                            legacyResourceId
                        }
                    }
                    fullyPaid
                    displayFinancialStatus
                    tags
                    email
                    number
                    createdAt
                    app {
                        name
                    }
                    customer {
                        firstName
                        lastName
                        id
                    }
                    transactions {
                        gateway
                        paymentId
                    }
                    shippingAddress {
                        firstName
                        lastName
                        company
                        address1
                        address2
                        province
                        city
                        country
                        phone
                        zip
                        formatted
                    }
                    billingAddress {
                        firstName
                        lastName
                        company
                        address1
                        address2
                        province
                        country
                        city
                        phone
                        zip
                        formatted
                    }
                    shippingLine {
                        originalPriceSet {
                            shopMoney {
                                amount
                                currencyCode
                            }
                        }
                    }
                }
            }
        }
        """
        variables = self.Variables(search_query=f'name:#{order_number}').model_dump(exclude_none=True)
        orders_json = await self._execute_query(query, **variables)
        try:
            orders_response = OrdersResponse(**orders_json)
            await self.get_order_line_items(orders_response.data.orders.nodes[0])
        except ValidationError as e:
            msg = f'{type(e)} {OrdersResponse.__name__}'
            msg += f'\n{repr(e.errors())}'
            exception = ShopifyException(url=self.host, payload=self.payload, response=orders_json, msg=msg)
            raise exception
        except KeyError:
            msg = 'KeyError'
            exception = ShopifyException(url=self.host, payload=self.payload, response=orders_json, msg=msg)
            raise exception
        except IndexError:
            msg = 'IndexError'
            exception = ShopifyException(url=self.host, payload=self.payload, response=orders_json, msg=msg)
            raise exception

        return orders_response.data.orders.nodes[0]

    async def get_products(self, batch_size: int = 10) -> list[Product]:
        """Función principal optimizada con procesamiento en lotes de 5 productos"""
        # Obtener todos los productos
        product_response = await self._get_products_base()
        products = product_response.data.products.nodes

        for i in range(0, len(products), batch_size):
            batch = products[i : i + batch_size]
            # Procesar cada lote de productos concurrentemente
            await gather(*[self.get_porduct_variant_inventory_levels(product) for product in batch])

        # Guardar resultados
        if config.environment == 'development':
            output_json = product_response.model_dump_json(indent=2)
            with open('shopify_inventory_data.json', 'w', encoding='utf-8') as f:
                f.write(output_json)

        return products


class ShopifyInventario:
    async def crear_bodega(self, location: Location) -> Bodega:
        async for session in get_async_session():
            async with session:
                bodega_query = BodegaQuery()

                bodega = await bodega_query.get_by_shopify_id(session, location.legacyResourceId)
                if bodega is None:
                    ubicacion = ', '.join(location.address.formatted)
                    bodega_create = BodegaCreate(ubicacion=ubicacion, shopify_id=location.legacyResourceId)
                    bodega = await bodega_query.create(session, bodega_create)

            return bodega
        raise

    async def crear_bodegas(self, locations: list[Location]):
        async for session in get_async_session():
            async with session:
                bodegas = [await self.crear_bodega(location) for location in locations]
                bodegas = [bodega for bodega in bodegas if bodega]
                return bodegas

    async def crear_elemento(self, product: Product) -> Elemento:
        async for session in get_async_session():
            async with session:
                elemento_query = ElementoQuery()
                elemento = await elemento_query.get_by_shopify_id(session, product.legacyResourceId)
                if elemento is None:
                    elemento_create = ElementoCreate(
                        shopify_id=product.legacyResourceId,
                        nombre=product.title,
                        tipo_medida_id=1,
                        grupo_id=3,
                        fabricado=True,
                    )
                    elemento = await elemento_query.create(session, elemento_create)

            return elemento
        raise

    async def crear_variante_elemento(self, variant: Variant, elemento_id: int) -> VarianteElemento:
        async for session in get_async_session():
            async with session:
                variante_elemento_query = VarianteElementoQuery()

                variante = await variante_elemento_query.get_by_shopify_id(session, variant.legacyResourceId)
                if variante is None:
                    variante_create = VarianteElementoCreate(
                        shopify_id=variant.legacyResourceId,
                        nombre=variant.title,
                        sku=variant.sku,
                        elemento_id=elemento_id,
                    )
                    variante = await variante_elemento_query.create(session, variante_create)

            return variante
        raise

    async def crear_precio_variante(self, price_variant: float, variante_elemento_id: int) -> PreciosPorVariante:
        async for session in get_async_session():
            async with session:
                precio_variante_query = PrecioPorVarianteQuery()

                precio = await precio_variante_query.get_last(session, variante_elemento_id, 1)
                if precio is None or (precio and precio.precio != price_variant):
                    precio_create = PreciosPorVarianteCreate(
                        variante_id=variante_elemento_id,
                        tipo_precio_id=1,
                        precio=price_variant,
                    )
                    precio = await precio_variante_query.create(session, precio_create)

            return precio
        raise

    async def crear_movimiento(
        self, bodega_id: int, variante_id: int, cantidad: int, tipo_movimiento_id: int = 1, estado_variante_id: int = 1
    ) -> Movimiento:
        async for session in get_async_session():
            async with session:
                movimiento_query = MovimientoQuery()

                movimiento_create = MovimientoCreate(
                    tipo_movimiento_id=tipo_movimiento_id,
                    variante_id=variante_id,
                    estado_variante_id=estado_variante_id,
                    cantidad=cantidad,
                    bodega_id=bodega_id,
                )
                movimiento = await movimiento_query.create(session, movimiento_create)

            return movimiento
        raise

    def get_products_unique_locations(self, products: list[Product]) -> dict[int, Location]:
        return {
            level.location.legacyResourceId: level.location
            for product in products
            for variant in product.variants
            for level in variant.inventoryItem.inventoryLevels.nodes
        }

    async def create_all(self, product: Product):
        elemento = await self.crear_elemento(product)
        for variant in product.variants:
            variante_elemento = await self.crear_variante_elemento(variant=variant, elemento_id=elemento.id)
            await self.crear_precio_variante(variant.price, variante_elemento.id)

    async def create_all_and_movimiento(self, product: Product, bodegas: list[Bodega]):
        elemento = await self.crear_elemento(product)
        for variant in product.variants:
            variante_elemento = await self.crear_variante_elemento(variant=variant, elemento_id=elemento.id)
            await self.crear_precio_variante(variant.price, variante_elemento.id)
            for level in variant.inventoryItem.inventoryLevels.nodes:
                bodega = next((bodega for bodega in bodegas if bodega.shopify_id == level.location.legacyResourceId))
                cantidad = level.quantities[0].quantity
                await self.crear_movimiento(bodega.id, variante_elemento.id, cantidad)

    async def sicnronizar_inventario(self):
        client = ShopifyGraphQLClient()
        products = await client.get_products()

        unique_locations = self.get_products_unique_locations(products)
        bodegas: list[Bodega] = []
        for location in unique_locations.values():
            bodega = await self.crear_bodega(location)
            bodegas.append(bodega)

        await gather(*[self.create_all_and_movimiento(product, bodegas) for product in products])

    async def crear_movimientos(self, ordenes: list[Order]):
        movimiento_query = MovimientoQuery()
        tipo_movimiento_query = TipoMovimientoQuery()
        tipo_soporte_query = TipoSoporteQuery()
        variante_elemento_query = VarianteElementoQuery()
        estado_variante_query = EstadoVarianteQuery()
        bodega_query = BodegaQuery()
        async for session in get_async_session():
            async with session:
                for orden in ordenes:
                    for item in orden.lineItems.nodes:
                        # Se garantiza que todos los elementos necesarios estén creados.
                        shopify_client = ShopifyGraphQLClient()
                        product = await shopify_client.get_product_by_variant_id(item.variant.legacyResourceId)
                        await shopify_client.get_porduct_variant_inventory_levels(product)
                        await self.create_all(product)

                        movimiento = await movimiento_query.get_by_soporte_id(
                            session, tipo_soporte_id=1, soporte_id=str(orden.number)
                        )

                        if movimiento is None:
                            variante_elemento = await variante_elemento_query.get_by_sku(session, item.sku)
                            if variante_elemento is None:
                                raise ValueError(f'No se pudo crear VarianteElemento con SKU {item.sku}')

                            tipo_movimiento = await tipo_movimiento_query.get_by_nombre(session, 'Salida')
                            tipo_soporte = await tipo_soporte_query.get_by_nombre(session, 'Pedido')
                            estado_variante = await estado_variante_query.get_by_nombre(session, 'Descontado')
                            bodega = None
                            if len(orden.fulfillments) > 0:
                                location_id = orden.fulfillments[0].location.legacyResourceId
                                bodega = await bodega_query.get_by_shopify_id(session, location_id)
                            else:
                                bodega = await bodega_query.get_by_shopify_id(
                                    session, 109793607972
                                )  # Por defecto si no se encuentra bodega, se asigna el ID del fulfillment en Bogotá
                            if bodega is None:
                                raise ValueError()

                            movimiento_create = MovimientoCreate(
                                tipo_movimiento_id=tipo_movimiento.id,
                                tipo_soporte_id=tipo_soporte.id,
                                soporte_id=str(orden.number),
                                variante_id=variante_elemento.id,
                                estado_variante_id=estado_variante.id,
                                cantidad=item.quantity,
                                bodega_id=bodega.id,
                                fecha=orden.createdAt,
                            )

                            await movimiento_query.create(session, movimiento_create)

    async def sincronizar_movimientos_by_range(self, start: date, end: date, step_days: int = 5):
        shopify_client = ShopifyGraphQLClient()
        # Realizar sincronización por rangos de fechas de acuerdo a step_days
        current_start = start
        while current_start < end:
            range_end = current_start + timedelta(days=step_days - 1)
            orders = await shopify_client.get_orders_by_range(current_start, min(range_end, end))
            current_start = range_end + timedelta(days=1)
            await self.crear_movimientos(orders)
            log_debug.debug(msg=f'movimientos sincronizados desde {current_start} hasta {range_end}')


if __name__ == '__main__':
    pass
    from asyncio import run
    # from time import time

    async def main():
        client = ShopifyGraphQLClient()

        # orders = await client.get_orders_by_range(date(2025, 7, 1), date(2025, 7, 31), 40)
        # await client.get_orders_line_items(orders.data.orders.nodes, 20)
        # with open('shopify_orders.json', 'w', encoding='utf-8') as f:
        #     f.write(orders.model_dump_json(exclude_unset=True, indent=2))

        # product_by_variant_id = await client.get_product_by_variant_id(45245052092708)
        # await client.get_porduct_variant_inventory_levels(product_by_variant_id)
        # print(product_by_variant_id.model_dump_json(exclude_unset=True, indent=2))

        # order_26492 = await client.get_order_by_number(26492)
        # assert order_26492.number == 26492
        # assert len(order_26492.data.orders.nodes[0].lineItems.nodes) > 0

        order_27588 = await client.get_order_by_number(27588)
        assert order_27588.number == 27588
        assert order_27588.fulfillments[0].location.legacyResourceId == 109793607972

        # order_9839649063204 = await client.get_order('gid://shopify/Order/9839649063204')
        # assert order_9839649063204.data.order.id == 'gid://shopify/Order/9839649063204'
        # print(order_9839649063204.model_dump_json(indent=2, exclude_unset=True))

        # await ShopifyInventario().sicnronizar_inventario()

        await ShopifyInventario().sincronizar_movimientos_by_range(date(2025, 9, 1), date(2025, 9, 15))

    run(main())
