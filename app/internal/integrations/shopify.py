import asyncio
from typing import Any
from pydantic import BaseModel
import aiohttp
from pandas import DataFrame, merge

from os.path import abspath
from sys import path as sys_path

sys_path.append(abspath('.'))

from app.models.db.inventario import Bodega, Elemento, Movimiento, PreciosPorVariante, VarianteElemento
from app.models.db.session import get_async_session
from app.models.pydantic.shopify.inventario import (
    InventoryLevel,
    InventoryLevelsResponse,
    Product,
    ProductsResponse,
    Variant,
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


class ShopifyGraphQLClient:
    def __init__(
        self,
        shop: str = config.shop_shopify,
        version: str = config.shop_version,
        access_token: str = config.api_key_shopify,
    ):
        self.shop_url = f'https://{shop}.myshopify.com/admin/api/{version}/graphql.json'
        self.access_token = access_token
        self.headers = {
            'Content-Type': 'application/json',
            'X-Shopify-Access-Token': access_token,
        }

    async def execute_query(self, query: str, **variables) -> dict:
        """Ejecuta una consulta GraphQL"""
        payload = {'query': query, 'variables': variables or {}}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.shop_url,
                headers=self.headers,
                json=payload,
            ) as response:
                return await response.json(encoding='utf-8')

    async def get_all_recursively(
        self,
        query: str,
        keys: list[str],
        variables: dict,
        result: dict | None = None,
    ):
        """
        :param keys: Lista de claves para acceder a los nodos y page_info de la respuesta
        """
        query_result = await self.execute_query(query, **variables)
        page_info = query_result.copy()

        for key in keys:
            page_info = page_info[key][0] if isinstance(page_info[key], list) else page_info[key]
        page_info = page_info['pageInfo']

        if result:
            nodes_query_result = query_result
            nodes_result = result
            for i in range(len(keys)):
                key = keys[i]
                nodes_query_result = (
                    nodes_query_result[key][0] if isinstance(nodes_query_result[key], list) else nodes_query_result[key]
                )
                nodes_result = nodes_result[key] if isinstance(nodes_result[key], list) else nodes_result[key]
                if i == len(keys) - 1:
                    nodes_query_result = nodes_query_result['nodes']
                    nodes_result = nodes_result['nodes']
                    nodes_query_result.extend(nodes_result)
        else:
            result = query_result

        if page_info.get('hasNextPage', False):
            variables['cursor'] = page_info.get('endCursor', None)
            return await self.get_all_recursively(query, keys, variables, query_result)

        return result


class QueryShopify:
    def __init__(self):
        self.client = ShopifyGraphQLClient()

    class Variables(BaseModel):
        num_items: int = 20
        cursor: str | None = None
        search_query: str | None = None
        id: int | None = None
        gid: str | None = None

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
        return await self.client.get_all_recursively(query, ['data', 'products'], variables)

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
        return await self.client.get_all_recursively(query, ['data', 'productVariants'], variables)

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
        return await self.client.get_all_recursively(
            query,
            ['data', 'inventoryItems', 'nodes', 'inventoryLevels'],
            variables,
        )

    async def get_order(self, order_gid: str, num_items: int = 40):
        query = """
        query GetOrder($gid: ID!, $num_items: Int!) {
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
                },
                shippingLine {
                    originalPriceSet {
                        shopMoney {
                            amount
                            currencyCode
                        }
                    }
                }
                lineItems(first:$num_items) {
                    nodes {
                        name
                        quantity
                        sku
                        originalUnitPriceSet {
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
        variables = self.Variables(gid=order_gid, num_items=num_items).model_dump(exclude_none=True)
        return await self.client.execute_query(query, **variables)


async def get_inventory_info():
    """Función principal optimizada con procesamiento concurrente por lotes"""
    query = QueryShopify()

    # Obtener todos los productos
    product_data = await query.get_products()
    product_response = ProductsResponse(**product_data)

    products = product_response.data.products.nodes
    batch_size = 10  # Procesar 10 productos por lote

    # Procesar productos en lotes
    for i in range(0, len(products), batch_size):
        batch_products = products[i : i + batch_size]

        # Recopilar IDs de productos válidos del lote
        product_ids = [product.legacyResourceId for product in batch_products]

        # Obtener todas las variantes del lote concurrentemente
        tasks = [query.get_variants(product_id) for product_id in product_ids]
        variants_results = await asyncio.gather(*tasks)
        variants_responses = [VariantsResponse(**result) for result in variants_results]

        # Mapear las respuestas por product_id
        variants_by_product_ids: dict[int, list[Variant]] = {}
        for response in variants_responses:
            for variant in response.data.productVariants.nodes:
                product_id = variant.product.legacyResourceId
                variants_by_product_ids[product_id] = variants_by_product_ids.get(product_id, []) + [variant]

        inventory_item_ids = []
        for product in batch_products:
            # Asignar variantes
            product.variants = variants_by_product_ids.get(product.legacyResourceId, [])
            # Agregar ids a inventory_item_ids
            inventory_item_ids.extend([variant.inventoryItem.legacyResourceId for variant in product.variants])

        # Obtener todos los niveles de inventario del lote concurrentemente
        tasks = [query.get_inventory_levels(item_id) for item_id in inventory_item_ids]
        inventory_levels_results = await asyncio.gather(*tasks)

        inventory_levels_responses = [InventoryLevelsResponse(**result) for result in inventory_levels_results]

        # Mapear los resultados de la consulta de niveles de inventario y sku por ID de variante
        inventory_levels_by_variant_id: dict[int, list[InventoryLevel]] = {}
        sku_by_variant_id: dict[int, str] = {}
        for response in inventory_levels_responses:
            for level in response.data.inventoryItems.nodes[0].inventoryLevels.nodes:
                variant_id = level.item.variant.legacyResourceId
                inventory_levels_by_variant_id[variant_id] = inventory_levels_by_variant_id.get(variant_id, []) + [
                    level
                ]
                sku_by_variant_id[variant_id] = response.data.inventoryItems.nodes[0].sku

        # Asignar niveles de inventario y sku a las variantes
        for product in batch_products:
            for variant in product.variants:
                variant.inventoryLevels = inventory_levels_by_variant_id.get(variant.legacyResourceId, [])
                variant.sku = sku_by_variant_id.get(variant.legacyResourceId, '')

    # Guardar resultados
    output_json = product_response.model_dump_json(indent=2)
    with open('shopify_inventory_data.json', 'w', encoding='utf-8') as f:
        f.write(output_json)

    return products


async def process_inventory_info(products: list[Product]):
    # df Bodegas
    bodegas_df = DataFrame(columns=['shopify_id', 'variante_shopify_id', 'variante_id', 'ubicacion'])
    variantes_df = DataFrame(columns=['nombre', 'shopify_id', 'product_shopify_id'])
    elementos_df = DataFrame(columns=['shopify_id', 'nombre', 'tipo_medida_id', 'grupo_id', 'descripcion', 'fabricado'])
    precios_variante_df = DataFrame(columns=['variante_shopify_id', 'tipo_precio_id', 'precio'])
    movimientos_df = DataFrame(
        columns=[
            'tipo_movimiento_id',
            'variante_shopify_id',
            'estado_variante_id',
            'cantidad',
            'bodega_shopify_id',
        ]
    )

    for product in products:
        elementos_df.loc[len(elementos_df)] = [
            product.legacyResourceId,
            product.title,
            1,
            3,
            None,
            True,
        ]

        for variante in product.variants:
            # ['nombre', 'shopify_id', 'product_shopify_id']
            variantes_df.loc[len(variantes_df)] = [
                variante.title,
                variante.legacyResourceId,
                product.legacyResourceId,
            ]

            # ['variante_shopify_id', 'tipo_precio_id', 'precio']
            precios_variante_df.loc[len(precios_variante_df)] = [
                variante.legacyResourceId,
                1,
                variante.price,
            ]

            for level in variante.inventoryLevels:
                address = level.location.address.address1
                city = level.location.address.city
                province = level.location.address.province
                country = level.location.address.country
                bodega = bodegas_df.loc[bodegas_df['shopify_id'] == level.location.legacyResourceId]
                ubicacion = ', '.join([str(x) for x in [address, city, province, country] if x])
                if bodega.empty:
                    bodegas_df.loc[len(bodegas_df)] = [
                        level.location.legacyResourceId,
                        variante.legacyResourceId,
                        None,
                        ubicacion,
                    ]

                cantidad = level.quantities[0].quantity
                # ['tipo_movimiento_id', 'variante_shopify_id', 'estado_variante_id', 'cantidad', 'bodega_shopify_id']
                movimientos_df.loc[len(movimientos_df)] = [
                    1,
                    variante.legacyResourceId,
                    1,
                    cantidad,
                    level.location.legacyResourceId,
                ]

    session_gen = get_async_session()
    session: AsyncSession = await anext(session_gen)

    # Consultar y crear bodegas
    bodegas_shopify_ids = bodegas_df.shopify_id.to_list()
    bodegas_db = await bodega_query.get_by_shopify_ids(session, bodegas_shopify_ids)
    if bodegas_df.shape[0] > 0:
        if len(bodegas_db) == 0:
            insert_records = bodegas_df.to_dict('records')
            insert_models = [Bodega(**{str(k): v for k, v in x.items()}) for x in insert_records]
            await bodega_query.bulk_insert(session, insert_models)
        else:
            bodegas_db_df = DataFrame([x.model_dump() for x in bodegas_db])
            bodegas_df = bodegas_df[~bodegas_df['shopify_id'].isin(bodegas_db_df['shopify_id'])]
            if bodegas_df.shape[0] > 0:
                insert_records = bodegas_df.to_dict('records')
                insert_models = [Bodega(**{str(k): v for k, v in x.items()}) for x in insert_records]
                await bodega_query.bulk_insert(session, insert_models)

    bodegas_db = await bodega_query.get_by_shopify_ids(session, bodegas_shopify_ids)
    bodegas_db_df = DataFrame([x.model_dump() for x in bodegas_db])

    # Consultar y crear/actualizar elementos
    elementos_shopify_ids = elementos_df.shopify_id.to_list()
    elementos_db = await elemento_query.get_by_shopify_ids(session, elementos_shopify_ids)
    if elementos_df.shape[0] > 0:
        if len(elementos_db) == 0:
            insert_records = elementos_df.to_dict('records')
            insert_models = [Elemento(**{str(k): v for k, v in x.items()}) for x in insert_records]
            await elemento_query.bulk_insert(session, insert_models)
        else:
            elementos_db_df = DataFrame([x.model_dump() for x in elementos_db])
            elementos_df = elementos_df[~elementos_df['shopify_id'].isin(elementos_db_df['shopify_id'])]
            if elementos_df.shape[0] > 0:
                insert_records = elementos_df.to_dict('records')
                insert_models = [Elemento(**{str(k): v for k, v in x.items()}) for x in insert_records]
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
    variantes_df = variantes_df.rename(columns={'id': 'elemento_id'})
    variantes_shopify_ids = variantes_df.shopify_id.to_list()
    variantes_db = await variante_elemento_query.get_by_shopify_ids(session, variantes_shopify_ids)
    if variantes_df.shape[0] > 0:
        if len(variantes_db) == 0:
            insert_records = variantes_df.to_dict('records')
            insert_models = [VarianteElemento(**{str(k): v for k, v in x.items()}) for x in insert_records]
            await variante_elemento_query.bulk_insert(session, insert_models)
        else:
            variantes_db_df = DataFrame([x.model_dump() for x in variantes_db])
            variantes_df = variantes_df[~variantes_df['shopify_id'].isin(variantes_db_df['shopify_id'])]
            if variantes_df.shape[0] > 0:
                insert_records = variantes_df.to_dict('records')
                insert_models = [VarianteElemento(**{str(k): v for k, v in x.items()}) for x in insert_records]
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
    )
    precios_variante_df = precios_variante_df.drop(columns=['shopify_id'])
    precios_variante_df = precios_variante_df.rename(columns={'id': 'variante_id'})
    variante_ids = precios_variante_df.variante_id.to_list()
    precio_varaintes_db = await precio_variante_query.get_lasts(session, variante_ids, 1)
    if precios_variante_df.shape[0] > 0:
        if len(precio_varaintes_db) == 0:
            insert_records = precios_variante_df.to_dict('records')
            insert_models = [PreciosPorVariante(**{str(k): v for k, v in x.items()}) for x in insert_records]
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
            if precios_variante_df.shape[0] > 0:
                insert_records = precios_variante_df.to_dict('records')
                insert_models = [PreciosPorVariante(**{str(k): v for k, v in x.items()}) for x in insert_records]
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
    )
    movimientos_df = movimientos_df.drop(columns=['shopify_id'])
    movimientos_df = movimientos_df.rename(columns={'id': 'variante_id'})
    movimientos_df = merge(
        movimientos_df,
        bodegas_db_df[['shopify_id', 'id']],
        left_on='bodega_shopify_id',
        right_on='shopify_id',
        how='left',
    )
    movimientos_df = movimientos_df.drop(columns=['shopify_id'])
    movimientos_df = movimientos_df.rename(columns={'id': 'bodega_id'})
    movimientos_db = await movimiento_query.get_by_varante_ids(session, variante_ids)
    movimientos_db_df = DataFrame([x.model_dump() for x in movimientos_db])
    movimientos_db_df = movimientos_db_df.groupby(['variante_id', 'bodega_id']).agg(
        {
            'cantidad': 'sum',
        }
    )
    movimientos_db_df = movimientos_db_df.reset_index()
    if movimientos_df.shape[0] > 0:
        if len(movimientos_db) == 0:
            insert_records = movimientos_df.to_dict('records')
            insert_models = [Movimiento(**{str(k): v for k, v in x.items()}) for x in insert_records]
            await movimiento_query.bulk_insert(session, insert_models)
        else:
            movimientos_db = movimientos_df.merge(
                movimientos_db_df[['variante_id', 'bodega_id', 'cantidad']],
                on=['variante_id', 'bodega_id'],
                how='left',
                suffixes=('', '_db'),
            )
            movimientos_db['diferencia'] = movimientos_db['cantidad'] - movimientos_db['cantidad_db']
            movimientos_db = movimientos_db[movimientos_db['diferencia'] != 0]
            if movimientos_db.shape[0] > 0:
                insert_records = movimientos_db.to_dict('records')
                insert_models = [Movimiento(**{str(k): v for k, v in x.items()}) for x in insert_records]
                await movimiento_query.bulk_insert(session, insert_models)

    # Cerrar la sesión
    await session.aclose()


async def main():
    products = await get_inventory_info()
    await process_inventory_info(products)


if __name__ == '__main__':
    asyncio.run(main())
