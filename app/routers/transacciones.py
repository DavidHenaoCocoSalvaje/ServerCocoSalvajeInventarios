from enum import Enum

from fastapi import APIRouter, Depends

from app.models.db.transacciones import Pedido
from app.routers.auth import validar_access_token
from app.routers.base import CRUD
from app.internal.query.transacciones import pedido_query


class Tags(Enum):
    INVENTARIO = 'Inventario'
    SHOPIFY = 'Shopify'


router = APIRouter(
    prefix='/transacciones',
    tags=[Tags.INVENTARIO],
    responses={404: {'description': 'No encontrado'}},
    dependencies=[Depends(validar_access_token)],
)

CRUD[Pedido](
    router,
    pedido_query,
    'pedido',
)
