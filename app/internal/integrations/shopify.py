import asyncio
from typing import Any, List
from pydantic import BaseModel
import aiohttp

import os
import sys

from app.models.pydantic.shopify.inventario import (
    InventoryLevelsResponse,
    ProductsResponse,
    VariantsResponse,
)

sys.path.append(os.path.abspath("."))

from app.config import config


class ShopifyGraphQLClient:
    def __init__(
        self,
        shop: str = config.shop_shopify,
        version: str = config.shop_version,
        access_token: str = config.api_key_shopify,
    ):
        self.shop_url = f"https://{shop}.myshopify.com/admin/api/{version}/graphql.json"
        self.access_token = access_token
        self.headers = {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": access_token,
        }

    async def execute_query(self, query: str, **variables) -> dict:
        """Ejecuta una consulta GraphQL"""
        payload = {"query": query, "variables": variables or {}}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.shop_url,
                headers=self.headers,
                json=payload,
            ) as response:
                return await response.json(encoding="utf-8")

    async def get_all_recursively(
        self,
        query: str,
        keys: list,
        variables: dict,
        result: dict = {},
    ):
        """
        :param keys: Lista de claves para acceder a los nodos y page_info de la respuesta
        """
        query_result = await self.execute_query(query, **variables)
        page_info = query_result.copy()

        for key in keys:
            if isinstance(page_info, list):
                page_info = page_info[0]
            page_info = page_info[key]
        page_info = page_info["pageInfo"]

        if result:
            nodes_keys = keys.copy()
            nodes_query_result = query_result
            nodes_result = result
            for i in range(len(nodes_keys)):
                key = nodes_keys[i]
                nodes_query_result = nodes_query_result[key]
                nodes_result = nodes_result[key]
                if i == len(nodes_keys) - 1:
                    nodes_query_result = nodes_query_result["nodes"]
                    nodes_result = nodes_result["nodes"]
                    nodes_query_result.extend(nodes_result)
        else:
            result = query_result

        if page_info.get("hasNextPage", False):
            variables["cursor"] = page_info.get("endCursor", None)
            return await self.get_all_recursively(query, keys, variables, query_result)

        return result


class QueriesShopify:
    def __init__(self):
        self.client = ShopifyGraphQLClient()

    class Variables(BaseModel):
        num_items: int = 20
        cursor: str | None = None
        search_query: str | None = None
        inventory_item_id: int | None = None

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
        return await self.client.get_all_recursively(
            query, ["data", "products"], variables
        )

    async def get_variants(self, product_id: int):
        query = """
            query GetVariants($num_items: Int!, $search_query: String!, $cursor: String) {
                productVariants(first: $num_items, after: $cursor, query: $search_query) {
                    nodes {
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
        variables = self.Variables(search_query=f"product_id:{product_id}").model_dump(
            exclude_none=True
        )
        return await self.client.get_all_recursively(
            query, ["data", "productVariants"], variables
        )

    async def get_inventory_levels(self, inventory_item_id: int):
        query = """
            query GetInventoryLevels($num_items: Int!, $search_query: String!, $cursor: String) {
                inventoryItems(first: 1 query: $search_query) {
                    nodes {
                        inventoryLevels(first:$num_items, after: $cursor) {
                            nodes {
                                quantities(names: ["incoming", "available", "committed", "reserved", "damaged", "safety_stock", "quality_control"]) {
                                    name
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
        variables = self.Variables(
            search_query=f"inventory_item_id:{inventory_item_id}"
        ).model_dump(exclude_none=True)
        return await self.client.get_all_recursively(
            query,
            ["data", "inventoryItems", "nodes", "inventoryLevels"],
            variables,
        )


async def get_inventory_info():
    async def process_product_variants(
        query_client: QueriesShopify, product_ids: List[int]
    ) -> dict:
        """Procesa variantes de múltiples productos concurrentemente"""
        tasks = [query_client.get_variants(product_id) for product_id in product_ids]
        results = await asyncio.gather(*tasks)

        # Mapear resultados por product_id
        variants_by_product = {}
        for i, result in enumerate(results):
            variant_response = VariantsResponse(**result)
            variants_by_product[product_ids[i]] = (
                variant_response.data.productVariants.nodes
            )

        return variants_by_product

    async def process_inventory_levels(
        query_client: QueriesShopify, inventory_item_ids: List[int]
    ) -> dict:
        """Procesa niveles de inventario de múltiples items concurrentemente"""
        tasks = [
            query_client.get_inventory_levels(item_id) for item_id in inventory_item_ids
        ]
        results = await asyncio.gather(*tasks)

        # Mapear resultados por inventory_item_id
        inventory_by_item = {}
        for i, result in enumerate(results):
            inventory_response = InventoryLevelsResponse(**result)
            inventory_levels = []
            if (
                inventory_response.data.inventoryItems.nodes
                and len(inventory_response.data.inventoryItems.nodes) > 0
            ):
                inventory_levels = inventory_response.data.inventoryItems.nodes[
                    0
                ].inventoryLevels.nodes
            inventory_by_item[inventory_item_ids[i]] = inventory_levels

        return inventory_by_item

    """Función principal optimizada con procesamiento concurrente por lotes"""
    query = QueriesShopify()

    # Obtener todos los productos
    product_data = await query.get_products()
    product_response = ProductsResponse(**product_data)

    products = product_response.data.products.nodes
    batch_size = 10  # Procesar 10 productos por lote

    # Procesar productos en lotes
    for i in range(0, len(products), batch_size):
        batch = products[i : i + batch_size]

        # Recopilar IDs de productos válidos del lote
        product_ids = [p.legacyResourceId for p in batch if p.legacyResourceId]

        if not product_ids:
            continue

        # Obtener todas las variantes del lote concurrentemente
        variants_by_product = await process_product_variants(query, product_ids)

        # Recopilar todos los inventory_item_ids del lote
        inventory_item_ids = []
        for product_id in product_ids:
            variants = variants_by_product.get(product_id, [])
            for variant in variants:
                if variant.inventoryItem and variant.inventoryItem.legacyResourceId:
                    inventory_item_ids.append(variant.inventoryItem.legacyResourceId)

        # Obtener todos los niveles de inventario del lote concurrentemente
        inventory_by_item = {}
        if inventory_item_ids:
            inventory_by_item = await process_inventory_levels(
                query, inventory_item_ids
            )

        # Asignar datos a las variantes del lote
        for product in batch:
            if not product.legacyResourceId:
                product.variants = []
                continue

            # Asignar variantes
            variants = variants_by_product.get(product.legacyResourceId, [])
            product.variants = variants

            # Asignar niveles de inventario a las variantes
            for variant in variants:
                if variant.inventoryItem and variant.inventoryItem.legacyResourceId:
                    variant.inventory_levels = inventory_by_item.get(
                        variant.inventoryItem.legacyResourceId, []
                    )

    return products
    # output_json = product_response.model_dump_json(indent=2)
    # with open("shopify_inventory_data.json", "w", encoding="utf-8") as f:
    #     f.write(output_json)

    # print("Shopify inventario procesado exitosamente")


if __name__ == "__main__":
    asyncio.run(get_inventory_info())
