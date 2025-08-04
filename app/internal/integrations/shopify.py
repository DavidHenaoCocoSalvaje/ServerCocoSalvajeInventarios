import asyncio
from typing import Any
from pydantic import BaseModel
import aiohttp
import json

import os
import sys

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


# products_data = get_shopify_products(False)
# products_data = get_shopify_products(True)
async def main():
    query = QueriesShopify()
    product_data = await query.get_products()
    product_data["data"]["products"] = []
    for node in product_data["data"]["products"]["nodes"]:
        variants_data = await query.get_variants(node["legacyResourceId"])
        


asyncio.run(
    main(),
)
