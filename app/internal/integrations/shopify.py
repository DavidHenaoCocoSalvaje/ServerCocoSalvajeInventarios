import json
import requests

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

    def execute_query(self, query: str, **variables) -> dict:
        """Ejecuta una consulta GraphQL"""
        payload = {"query": query, "variables": variables or {}}

        response = requests.post(
            self.shop_url,
            headers=self.headers,
            json=payload,
        )

        return response.json()

    def get_all_recursively(
        self,
        query: str,
        keys: list,
        variables: dict = {"numItems": 20, "cursor": ""},
        chunk: dict = {},
    ) -> dict:
        chunk = self.execute_query(query, **variables)
        page_info = {}
        for key in keys:
            page_info = chunk["data"][key]
        has_next_page = page_info.get("hasNextPage", False)
        variables["cursor"] = page_info.get("endCursor", "")
        if has_next_page:
            self.get_all_recursively(query, keys, variables, chunk)
        return chunk


def get_shopify_products(recursive: bool = True):
    """
    Fetches products from Shopify using the GraphQL API.
    """
    query = """
    query GetProducts($numItems: Int!, $cursor: String) {
        products(first: $numItems, after: $cursor) {
            nodes {
                id
            }
            pageInfo {
                hasNextPage
                endCursor
            }
        }
    }
    """
    variables = {"numItems": 5, "cursos": ""}
    client = ShopifyGraphQLClient()
    if recursive:
        return client.get_all_recursively(query, ["products"], **variables)
    else:
        return client.execute_query(query, **variables)


# Example usage


products_data = get_shopify_products(False)
# recursive_products_data = get_shopify_products(True)

if products_data:
    print(json.dumps(products_data, indent=4))
    print(len(products_data["products"]["nodes"]))
    # print(json.dumps(recursive_products_data, indent=4))
