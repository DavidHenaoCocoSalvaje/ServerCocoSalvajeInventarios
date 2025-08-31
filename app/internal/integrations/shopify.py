import traceback
from typing import Any
from pydantic import BaseModel
from pandas import DataFrame, merge, isna
from asyncio import sleep
from time import time
from re import findall


if __name__ == '__main__':
    from os.path import abspath
    from sys import path as sys_path

    sys_path.append(abspath('.'))

from app.internal.log import factory_logger

from app.internal.integrations.base import BaseClient, ClientException
from app.models.db.inventario import Bodega, Elemento, Movimiento, PreciosPorVariante, VarianteElemento
from app.models.db.session import get_async_session
from app.models.pydantic.shopify.inventario import (
    InventoryLevelsResponse,
    Product,
    ProductsResponse,
    VariantsResponse,
)
from app.internal.query.inventario import (
    bodega_query,
    elemento_query,
    variante_elemento_query,
    precio_variante_query,
    movimiento_query,
)
from sqlalchemy.ext.asyncio import AsyncSession


from app.config import config

log_shopify = factory_logger('shopify', file=True)


class ShopifyException(ClientException):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ShopifyGraphQLClient(BaseClient):
    __instance = None
    _last_request_time: float = 0
    _min_interval: float = 1.0

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
        super().__init__()
        self.host = f'https://{shop}.myshopify.com/admin/api/{version}/graphql.json'
        self.access_token = access_token
        self.headers = {
            'Content-Type': 'application/json',
            'X-Shopify-Access-Token': access_token,
        }
        self.payload = {}
        self.response = {}

    async def _rate_limit(self):
        """Aplica rate limiting para asegurar 1 petición por segundo"""
        current_time = time()
        time_since_last_request = current_time - self._last_request_time

        if time_since_last_request < self._min_interval:
            sleep_time = self._min_interval - time_since_last_request
            await sleep(sleep_time)

        self._last_request_time = time()

    async def _execute_query(self, query: str, **variables) -> dict:
        """Ejecuta una consulta GraphQL con rate limiting"""
        # Aplicar rate limiting antes de la petición
        await self._rate_limit()

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
                msg = f'No se pudo obtener {key}'
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

    async def get_products(self) -> dict[str, Any]:
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
        return await self._get_all(query, ['data', 'products'], variables)

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
        return await self._get_all(query, ['data', 'productVariants'], variables)

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
        return await self._get_all(
            query,
            ['data', 'inventoryItems', 'nodes', 'inventoryLevels'],
            variables,
        )

    async def get_order(self, order_gid: str):
        query = """
        query GetOrder($gid: ID!) {
            order(id: $gid) {
                fullyPaid
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
        order_line_items_json = await self.get_order_line_items(order_gid)
        order = order_json.get('data', {}).get('order', {})
        line_items = order_line_items_json.get('data', {}).get('order', {}).get('lineItems', {})
        if not order:
            exception = ShopifyException(url=self.host, payload=self.payload, response=order_json)
            log_shopify.error(f'No se pudo obtener orden:{exception}')
            raise exception
        if not line_items:
            exception = ShopifyException(url=self.host, payload=self.payload, response=order_line_items_json)
            log_shopify.error(f'No se pudo obtener line_items:{exception}')
            raise exception

        order_json['data']['order']['lineItems'] = order_line_items_json['data']['order']['lineItems']
        return order_json

    async def get_order_line_items(self, order_gid: str):
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
                        discountedUnitPriceSet {
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


async def get_inventory_info(shopify_client: ShopifyGraphQLClient):
    """Función principal optimizada con procesamiento secuencial por producto"""
    # Obtener todos los productos
    product_data = await shopify_client.get_products()
    product_response = ProductsResponse(**product_data)

    products = product_response.data.products.nodes

    # Procesar cada producto individualmente
    for product in products:
        # Obtener variantes del producto actual
        variants_result = await shopify_client.get_variants(product.legacyResourceId)
        variants_response = VariantsResponse(**variants_result)

        # Asignar variantes al producto
        product.variants = variants_response.data.productVariants.nodes

        # Procesar cada variante del producto
        for variant in product.variants:
            inventory_item_id = variant.inventoryItem.legacyResourceId

            # Obtener niveles de inventario para esta variante específica
            inventory_levels_result = await shopify_client.get_inventory_levels(inventory_item_id)
            inventory_levels_response = InventoryLevelsResponse(**inventory_levels_result)

            # Asignar niveles de inventario y SKU a la variante
            if inventory_levels_response.data.inventoryItems.nodes:
                inventory_item = inventory_levels_response.data.inventoryItems.nodes[0]
                variant.inventoryLevels = inventory_item.inventoryLevels.nodes
                variant.sku = inventory_item.sku
            else:
                variant.inventoryLevels = []
                variant.sku = ''

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

    session_gen = get_async_session()
    session: AsyncSession = await anext(session_gen)

    # Consultar y crear bodegas
    bodegas_shopify_ids = bodegas_df.shopify_id.to_list()
    bodegas_db = await bodega_query.get_by_shopify_ids(session, bodegas_shopify_ids)
    if bodegas_df.shape[0] > 0:
        if not bodegas_db:
            insert_records = bodegas_df.to_dict('records')
            insert_models = [Bodega(**{str(k): v for k, v in x.items() if not isna(v)}) for x in insert_records]
            await bodega_query.bulk_insert(session, insert_models)
        else:
            bodegas_db_df = DataFrame([x.model_dump() for x in bodegas_db])
            bodegas_df = bodegas_df[~bodegas_df['shopify_id'].isin(bodegas_db_df['shopify_id'])]
            insert_records = bodegas_df.to_dict('records')
            insert_models = [Bodega(**{str(k): v for k, v in x.items() if not isna(v)}) for x in insert_records]
            await bodega_query.bulk_insert(session, insert_models)

    bodegas_db = await bodega_query.get_by_shopify_ids(session, bodegas_shopify_ids)
    bodegas_db_df = DataFrame([x.model_dump() for x in bodegas_db])

    # Consultar y crear/actualizar elementos
    elementos_shopify_ids = elementos_df.shopify_id.to_list()
    elementos_db = await elemento_query.get_by_shopify_ids(session, elementos_shopify_ids)
    if elementos_df.shape[0] > 0:
        if not elementos_db:
            insert_records = elementos_df.to_dict('records')
            insert_models = [Elemento(**{str(k): v for k, v in x.items() if not isna(v)}) for x in insert_records]
            await elemento_query.bulk_insert(session, insert_models)
        else:
            elementos_db_df = DataFrame([x.model_dump() for x in elementos_db])
            elementos_df = elementos_df[~elementos_df['shopify_id'].isin(elementos_db_df['shopify_id'])]
            insert_records = elementos_df.to_dict('records')
            insert_models = [Elemento(**{str(k): v for k, v in x.items() if not isna(v)}) for x in insert_records]
            await elemento_query.bulk_insert(session, insert_models)

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
    variantes_db = await variante_elemento_query.get_by_shopify_ids(session, variantes_shopify_ids)
    if variantes_df.shape[0] > 0:
        if not variantes_db:
            insert_records = variantes_df.to_dict('records')
            insert_models = [
                VarianteElemento(**{str(k): v for k, v in x.items() if not isna(v)}) for x in insert_records
            ]
            await variante_elemento_query.bulk_insert(session, insert_models)
        else:
            variantes_db_df = DataFrame([x.model_dump() for x in variantes_db])
            variantes_df = variantes_df[~variantes_df['shopify_id'].isin(variantes_db_df['shopify_id'])]
            insert_records = variantes_df.to_dict('records')
            insert_models = [
                VarianteElemento(**{str(k): v for k, v in x.items() if not isna(v)}) for x in insert_records
            ]
            await variante_elemento_query.bulk_insert(session, insert_models)

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
    precio_varaintes_db = await precio_variante_query.get_lasts(session, variante_ids, 1)
    if precios_variante_df.shape[0] > 0:
        if not precio_varaintes_db:
            insert_records = precios_variante_df.to_dict('records')
            insert_models = [
                PreciosPorVariante(**{str(k): v for k, v in x.items() if not isna(v)}) for x in insert_records
            ]
            await precio_variante_query.bulk_insert(session, insert_models)
        else:
            precio_varaintes_db_df = DataFrame([x.model_dump() for x in precio_varaintes_db])
            # Comparar precio de la bd con el de shopify
            precios_variante_df = precios_variante_df.merge(
                precio_varaintes_db_df[['variante_id', 'precio']],
                on='variante_id',
                how='left',
                suffixes=('', '_db'),
            )
            precios_variante_df['nuevo_precio'] = precios_variante_df['precio'] != precios_variante_df['precio_db']
            precios_variante_df = precios_variante_df[precios_variante_df['nuevo_precio']]
            insert_records = precios_variante_df.to_dict('records')
            insert_models = [
                PreciosPorVariante(**{str(k): v for k, v in x.items() if not isna(v)}) for x in insert_records
            ]
            await precio_variante_query.bulk_insert(session, insert_models)

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
    movimientos_db = await movimiento_query.get_by_varante_ids(session, variante_ids)
    if movimientos_df.shape[0] > 0:
        if not movimientos_db:
            insert_records = movimientos_df.to_dict('records')
            insert_models = [Movimiento(**{str(k): v for k, v in x.items() if not isna(v)}) for x in insert_records]
            await movimiento_query.bulk_insert(session, insert_models)
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
            insert_records = movimientos_db.to_dict('records')
            insert_models = [Movimiento(**{str(k): v for k, v in x.items() if not isna(v)}) for x in insert_records]
            await movimiento_query.bulk_insert(session, insert_models)

    # Cerrar la sesión
    await session.aclose()


if __name__ == '__main__':
    from asyncio import run

    async def main():
        client = ShopifyGraphQLClient()
        products = await get_inventory_info(client)
        await persistir_inventory_info(products)

    run(main())
