import traceback
from pydantic import BaseModel, ValidationError
from pandas import DataFrame, merge, isna
from re import findall
from asyncio import gather


if __name__ == '__main__':
    from os.path import abspath
    from sys import path as sys_path

    sys_path.append(abspath('.'))

from app.internal.query.inventario import (
    BodegaQuery,
    ElementoQuery,
    MovimientoQuery,
    PrecioPorVarianteQuery,
    VarianteElementoQuery,
)

from app.internal.log import factory_logger, LogLevel
from app.models.pydantic.shopify.order import OrderResponse, OrdersResponse
from app.internal.integrations.base import BaseClient, ClientException
from app.models.db.inventario import Bodega, Elemento, Movimiento, PreciosPorVariante, VarianteElemento
from app.models.db.session import get_async_session
from app.models.pydantic.shopify.inventario import (
    InventoryLevelsResponse,
    Product,
    ProductsResponse,
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

    async def get_products(self) -> ProductsResponse:
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

    async def get_variants(self, product_id: int):
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
        inventory_levels_json = await self._get_all(
            query,
            ['data', 'inventoryItems', 'nodes', 'inventoryLevels'],
            variables,
        )
        return InventoryLevelsResponse(**inventory_levels_json)

    async def _get_order_line_items(self, order_gid: str):
        query = """
        query GetLineItemsOrder($gid: ID!, $num_items: Int!, $cursor: String) {
            order(id: $gid) {
                lineItems(first:$num_items, after: $cursor) {
                    nodes {
                        name
                        quantity
                        sku
                        variant {
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
        variables = self.Variables(gid=order_gid).model_dump(exclude_none=True)
        return await self._get_all(query, ['data', 'order', 'lineItems'], variables)

    async def get_order(self, order_gid: str) -> OrderResponse:
        query = """
        query GetOrder($gid: ID!) {
            order(id: $gid) {
                id
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
        order_line_items_json = await self._get_order_line_items(order_gid)
        try:
            order_json['data']['order']['lineItems'] = order_line_items_json['data']['order']['lineItems']
            order_response = OrderResponse(**order_json)
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

    async def get_order_by_number(self, order_number: int):
        query = """
        query GetOrderByNumber($search_query: String!) {
            orders(first: 1, query: $search_query) {
                nodes {
                    id
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
            gid = orders_json['data']['orders']['nodes'][0]['id']
            order_line_items_json = await self._get_order_line_items(gid)
            orders_json['data']['orders']['nodes'][0]['lineItems'] = order_line_items_json['data']['order']['lineItems']
            orders_response = OrdersResponse(**orders_json)
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

        return orders_response

    async def get_inventory_info(self) -> list[Product]:
        """Función principal optimizada con procesamiento en lotes de 5 productos"""
        # Obtener todos los productos
        product_response = await self.get_products()
        products = product_response.data.products.nodes

        async def get_inventory_levels_product(product):
            # Obtener variantes del producto actual
            variants_response = await self.get_variants(product.legacyResourceId)

            # Asignar variantes al producto
            product.variants = variants_response.data.productVariants.nodes

            # Procesar cada variante del producto
            for variant in product.variants:
                inventory_item_id = variant.inventoryItem.legacyResourceId

                # Obtener niveles de inventario para esta variante específica
                inventory_levels_response = await self.get_inventory_levels(inventory_item_id)

                # Asignar niveles de inventario y SKU a la variante
                if inventory_levels_response.data.inventoryItems.nodes:
                    inventory_item = inventory_levels_response.data.inventoryItems.nodes[0]
                    variant.inventoryLevels = inventory_item.inventoryLevels.nodes
                    variant.sku = inventory_item.sku
                else:
                    variant.inventoryLevels = []
                    variant.sku = ''

        # Procesar productos en lotes de 5
        batch_size = 5
        for i in range(0, len(products), batch_size):
            batch = products[i : i + batch_size]

            # Procesar cada lote de productos concurrentemente
            await gather(*[get_inventory_levels_product(product) for product in batch])

        # Guardar resultados
        if config.environment == 'development':
            output_json = product_response.model_dump_json(indent=2)
            with open('shopify_inventory_data.json', 'w', encoding='utf-8') as f:
                f.write(output_json)

        return products


async def persistir_inventory_info(products: list[Product]):
    # df Bodegas
    bodega_model_keys = list(Bodega.model_json_schema()['properties'].keys())
    bodega_model_keys.extend(['variante_shopify_id', 'variante_id'])  # Columnas que no pertenecen a la tabla Bodega
    bodegas_df = DataFrame(columns=bodega_model_keys)

    variante_model_keys = list(VarianteElemento.model_json_schema()['properties'].keys())
    variante_model_keys.extend(['product_shopify_id'])  # Columnas que no pertenecen a la tabla VarianteElemento
    variantes_df = DataFrame(columns=variante_model_keys)

    elemento_model_keys = list(Elemento.model_json_schema()['properties'].keys())
    elementos_df = DataFrame(columns=elemento_model_keys)

    precio_model_keys = list(PreciosPorVariante.model_json_schema()['properties'].keys())
    precio_model_keys.extend(['variante_shopify_id'])  # Columnas que no pertenecen a la tabla PreciosPorVariante
    precios_variante_df = DataFrame(columns=precio_model_keys)

    movimiento_model_keys = list(Movimiento.model_json_schema()['properties'].keys())
    movimiento_model_keys.extend(
        ['variante_shopify_id', 'bodega_shopify_id']
    )  # Columnas que no pertenecen a la tabla Movimiento
    movimientos_df = DataFrame(columns=movimiento_model_keys)

    for product in products:
        elementos_df.loc[len(elementos_df)] = {  # type: ignore
            'shopify_id': product.legacyResourceId,
            'nombre': product.title,
            'tipo_medida_id': 1,
            'grupo_id': 3,
            'fabricado': True,
        }

        for variante in product.variants:
            variantes_df.loc[len(variantes_df)] = {  # type: ignore
                'nombre': variante.title,
                'sku': variante.sku,
                'shopify_id': variante.legacyResourceId,
                'product_shopify_id': product.legacyResourceId,
            }

            precios_variante_df.loc[len(precios_variante_df)] = {  # type: ignore
                'variante_shopify_id': variante.legacyResourceId,
                'tipo_precio_id': 1,
                'precio': variante.price,
            }

            for level in variante.inventoryLevels:
                address = level.location.address.address1
                city = level.location.address.city
                province = level.location.address.province
                country = level.location.address.country
                bodega = bodegas_df.loc[bodegas_df['shopify_id'] == level.location.legacyResourceId]
                ubicacion = ', '.join([str(x) for x in [address, city, province, country] if x])
                if bodega.empty:
                    bodegas_df.loc[len(bodegas_df)] = {  # type: ignore
                        'shopify_id': level.location.legacyResourceId,
                        'variante_shopify_id': variante.legacyResourceId,
                        'ubicacion': ubicacion,
                    }

                cantidad = level.quantities[0].quantity

                movimientos_df.loc[len(movimientos_df)] = {  # type: ignore
                    'tipo_movimiento_id': 1,
                    'variante_shopify_id': variante.legacyResourceId,
                    'estado_variante_id': 1,
                    'cantidad': cantidad,
                    'bodega_shopify_id': level.location.legacyResourceId,
                }

    async for session in get_async_session():
        async with session:
            # Consultar y crear bodegas
            bodegas_shopify_ids = bodegas_df.shopify_id.to_list()
            bodega_query = BodegaQuery()
            bodegas_db = await bodega_query.get_by_shopify_ids(session, bodegas_shopify_ids)
            if bodegas_df.shape[0] > 0:
                if not bodegas_db:
                    insert_records = bodegas_df.to_dict('records')
                    insert_models = [Bodega(**{str(k): v for k, v in x.items() if not isna(v)}) for x in insert_records]
                    await bodega_query.safe_bulk_insert(session, insert_models)
                else:
                    bodegas_db_df = DataFrame([x.model_dump() for x in bodegas_db])
                    bodegas_df = bodegas_df[~bodegas_df['shopify_id'].isin(bodegas_db_df['shopify_id'])]
                    insert_records = bodegas_df.to_dict('records')
                    insert_models = [Bodega(**{str(k): v for k, v in x.items() if not isna(v)}) for x in insert_records]
                    await bodega_query.safe_bulk_insert(session, insert_models)

            bodegas_db = await bodega_query.get_by_shopify_ids(session, bodegas_shopify_ids)
            bodegas_db_df = DataFrame([x.model_dump() for x in bodegas_db])

            # Consultar y crear/actualizar elementos
            elementos_shopify_ids = elementos_df.shopify_id.to_list()
            elemento_query = ElementoQuery()
            elementos_db = await elemento_query.get_by_shopify_ids(session, elementos_shopify_ids)
            if elementos_df.shape[0] > 0:
                if not elementos_db:
                    insert_records = elementos_df.to_dict('records')
                    insert_models = [
                        Elemento(**{str(k): v for k, v in x.items() if not isna(v)}) for x in insert_records
                    ]
                    await elemento_query.safe_bulk_insert(session, insert_models)
                else:
                    elementos_db_df = DataFrame([x.model_dump() for x in elementos_db])
                    elementos_df = elementos_df[~elementos_df['shopify_id'].isin(elementos_db_df['shopify_id'])]
                    insert_records = elementos_df.to_dict('records')
                    insert_models = [
                        Elemento(**{str(k): v for k, v in x.items() if not isna(v)}) for x in insert_records
                    ]
                    await elemento_query.safe_bulk_insert(session, insert_models)

            elementos_db = await elemento_query.get_by_shopify_ids(session, elementos_shopify_ids)
            elementos_db_df = DataFrame([x.model_dump() for x in elementos_db])

            # Consultar y crear/actualizar variantes
            variantes_df = merge(
                variantes_df,
                elementos_db_df[['shopify_id', 'id']],
                left_on='product_shopify_id',
                right_on='shopify_id',
                how='left',
                suffixes=('', '_elemento'),
            )
            variantes_df = variantes_df.drop(columns=['shopify_id_elemento'])
            variantes_df['elemento_id'] = variantes_df['id_elemento']
            variantes_df = variantes_df.drop(columns=['id_elemento'])
            variantes_shopify_ids = variantes_df.shopify_id.to_list()
            variante_elemento_query = VarianteElementoQuery()
            variantes_db = await variante_elemento_query.get_by_shopify_ids(session, variantes_shopify_ids)
            if variantes_df.shape[0] > 0:
                if not variantes_db:
                    insert_records = variantes_df.to_dict('records')
                    insert_models = [
                        VarianteElemento(**{str(k): v for k, v in x.items() if not isna(v)}) for x in insert_records
                    ]
                    await variante_elemento_query.safe_bulk_insert(session, insert_models)
                else:
                    variantes_db_df = DataFrame([x.model_dump() for x in variantes_db])
                    variantes_df = variantes_df[~variantes_df['shopify_id'].isin(variantes_db_df['shopify_id'])]
                    insert_records = variantes_df.to_dict('records')
                    insert_models = [
                        VarianteElemento(**{str(k): v for k, v in x.items() if not isna(v)}) for x in insert_records
                    ]
                    await variante_elemento_query.safe_bulk_insert(session, insert_models)

            variantes_db = await variante_elemento_query.get_by_shopify_ids(session, variantes_shopify_ids)
            variantes_db_df = DataFrame([x.model_dump() for x in variantes_db])

            # Consultar y crear/actualizar precios
            precios_variante_df = merge(
                precios_variante_df,
                variantes_db_df[['shopify_id', 'id']],
                left_on='variante_shopify_id',
                right_on='shopify_id',
                how='left',
                suffixes=('', '_variante'),
            )
            precios_variante_df = precios_variante_df.drop(columns=['shopify_id'])
            precios_variante_df['variante_id'] = precios_variante_df['id_variante']
            precios_variante_df = precios_variante_df.drop(columns=['id_variante'])
            variante_ids = precios_variante_df.variante_id.to_list()
            precio_variante_query = PrecioPorVarianteQuery()
            precio_varaintes_db = await precio_variante_query.get_lasts(session, variante_ids, 1)
            if precios_variante_df.shape[0] > 0:
                if not precio_varaintes_db:
                    insert_records = precios_variante_df.to_dict('records')
                    insert_models = [
                        PreciosPorVariante(**{str(k): v for k, v in x.items() if not isna(v)}) for x in insert_records
                    ]
                    await precio_variante_query.safe_bulk_insert(session, insert_models)
                else:
                    precio_varaintes_db_df = DataFrame([x.model_dump() for x in precio_varaintes_db])
                    # Comparar precio de la bd con el de shopify
                    precios_variante_df = precios_variante_df.merge(
                        precio_varaintes_db_df[['variante_id', 'precio']],
                        on='variante_id',
                        how='left',
                        suffixes=('', '_db'),
                    )
                    precios_variante_df['nuevo_precio'] = (
                        precios_variante_df['precio'] != precios_variante_df['precio_db']
                    )
                    precios_variante_df = precios_variante_df[precios_variante_df['nuevo_precio']]
                    insert_records = precios_variante_df.to_dict('records')
                    insert_models = [
                        PreciosPorVariante(**{str(k): v for k, v in x.items() if not isna(v)}) for x in insert_records
                    ]
                    await precio_variante_query.safe_bulk_insert(session, insert_models)

            precio_varaintes_db = await precio_variante_query.get_lasts(session, variante_ids, 1)
            precio_varaintes_db_df = DataFrame([x.model_dump() for x in precio_varaintes_db])

            # Consultar y crear/actualizar movimientos
            movimientos_df = merge(
                movimientos_df,
                variantes_db_df[['shopify_id', 'id']],
                left_on='variante_shopify_id',
                right_on='shopify_id',
                how='left',
                suffixes=('', '_variante'),
            )
            movimientos_df = movimientos_df.drop(columns=['shopify_id'])
            movimientos_df['variante_id'] = movimientos_df['id_variante']
            movimientos_df = movimientos_df.drop(columns=['id_variante'])
            movimientos_df = merge(
                movimientos_df,
                bodegas_db_df[['shopify_id', 'id']],
                left_on='bodega_shopify_id',
                right_on='shopify_id',
                how='left',
                suffixes=('', '_bodega'),
            )
            movimientos_df = movimientos_df.drop(columns=['shopify_id'])
            movimientos_df['bodega_id'] = movimientos_df['id_bodega']
            movimientos_df = movimientos_df.drop(columns=['id_bodega'])
            movimiento_query = MovimientoQuery()
            movimientos_db = await movimiento_query.get_by_varante_ids(session, variante_ids)
            if movimientos_df.shape[0] > 0:
                if not movimientos_db:
                    insert_records = movimientos_df.to_dict('records')
                    insert_models = [
                        Movimiento(**{str(k): v for k, v in x.items() if not isna(v)}) for x in insert_records
                    ]
                    await movimiento_query.safe_bulk_insert(session, insert_models)
                else:
                    movimientos_db_df = DataFrame([x.model_dump() for x in movimientos_db])
                    movimientos_db_df = movimientos_db_df.groupby(['variante_id', 'bodega_id']).agg(
                        {
                            'cantidad': 'sum',
                        }
                    )
                    movimientos_db_df = movimientos_db_df.reset_index()
                    movimientos_db = movimientos_df.merge(
                        movimientos_db_df[['variante_id', 'bodega_id', 'cantidad']],
                        on=['variante_id', 'bodega_id'],
                        how='left',
                        suffixes=('', '_db'),
                    )
                    movimientos_db['diferencia'] = movimientos_db['cantidad'] - movimientos_db['cantidad_db']
                    movimientos_db = movimientos_db[movimientos_db['diferencia'] != 0]
                    movimientos_df['cantidad'] = movimientos_db['diferencia']
                    insert_records = movimientos_db.to_dict('records')
                    insert_models = [
                        Movimiento(**{str(k): v for k, v in x.items() if not isna(v)}) for x in insert_records
                    ]
                    await movimiento_query.safe_bulk_insert(session, insert_models)


if __name__ == '__main__':
    from asyncio import run
    from time import time

    async def main():
        client = ShopifyGraphQLClient()
        ini_time = time()
        print(ini_time)
        products = await client.get_inventory_info()
        fin_time = time()
        print(fin_time, fin_time - ini_time)
        print(time())
        order_26492 = await client.get_order_by_number(26492)
        assert order_26492.data.orders.nodes[0].number == 26492
        assert len(order_26492.data.orders.nodes[0].lineItems.nodes) > 0

        await persistir_inventory_info(products)

    run(main())
