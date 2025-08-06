import asyncio
from typing import Any
from pydantic import BaseModel
import aiohttp

import os
import sys

sys.path.append(os.path.abspath("."))

from app.models.pydantic.shopify.inventario import (
    InventoryLevel,
    InventoryLevelsResponse,
    ProductsResponse,
    Variant,
    VariantsResponse,
)

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
    """Función principal optimizada con procesamiento concurrente por lotes"""
    query = QueriesShopify()

    # Obtener todos los productos
    product_data = await query.get_products()
    product_response = ProductsResponse(**product_data)

    products = product_response.data.products.nodes
    batch_size = 10  # Procesar 10 productos por lote

    # Procesar productos en lotes
    for i in range(0, len(products), batch_size):
        batch_products = products[i : i + batch_size]

        # Recopilar IDs de productos válidos del lote
        product_ids = [p.legacyResourceId for p in batch_products if p.legacyResourceId]

        if not product_ids:
            continue

        # Obtener todas las variantes del lote concurrentemente
        tasks = [query.get_variants(product_id) for product_id in product_ids]
        variants_results = await asyncio.gather(*tasks)

        # Mapear resultados por product_id
        variants_by_product: dict[int, list[Variant]] = {
            product_id: VariantsResponse(**result).data.productVariants.nodes
            for product_id, result in zip(product_ids, variants_results)
        }

        inventory_item_ids = []
        for product in batch_products:
            # Asignar variantes
            product.variants = variants_by_product.get(
                product.legacyResourceId or 0, []
            )
            # Recopilar todos los inventory_item_ids del lote
            inventory_item_ids.extend(
                [
                    variant.inventoryItem.legacyResourceId
                    for variant in product.variants
                    if variant.inventoryItem and variant.inventoryItem.legacyResourceId
                ]
            )

        tasks = [query.get_inventory_levels(item_id) for item_id in inventory_item_ids]
        inventory_levels_results = await asyncio.gather(*tasks)

        # Obtener todos los niveles de inventario del lote concurrentemente
        inventory_levels_by_item_id: dict[int, list[InventoryLevel]] = {
            item_id: InventoryLevelsResponse(**result)
            .data.inventoryItems.nodes[0]
            .inventoryLevels.nodes
            for item_id, result in zip(inventory_item_ids, inventory_levels_results)
        }

        # Asignar niveles de inventario a las variantes
        for product in batch_products:
            for variant in product.variants:
                variant.inventoryLevels = inventory_levels_by_item_id.get(
                    variant.inventoryItem.legacyResourceId or 0, []
                )

    # Guardar resultados
    output_json = product_response.model_dump_json(indent=2)
    with open("shopify_inventory_data.json", "w", encoding="utf-8") as f:
        f.write(output_json)

    print("Shopify inventario procesado exitosamente")
    return products


if __name__ == "__main__":
    asyncio.run(get_inventory_info())
