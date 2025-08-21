# app.models.pydantic.shopify.payloads

# Modelos de payloads enviados por Shopify en webhooks

from app.models.pydantic.base import Base


class Order(Base):
    id: int = 0
    admin_graphql_api_id: str = ''
    name: str = '' # Es el número de pedido que se ve en la interfaz de Shopify
    fullyPaid: bool = False
    
    