from fastapi import APIRouter, Depends, status

from app.internal.integrations.gemini import search_product_description
from app.internal.log import factory_logger
from app.routers.auth import validar_access_token


router = APIRouter(
    prefix='/search',
    responses={404: {'description': 'No encontrado'}},
    tags=['Search'],
    dependencies=[Depends(validar_access_token)],
)

log_search = factory_logger('search')


@router.get(
    '/bing',
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(validar_access_token)],
)
async def post_search_bing_copilot(
    query: str,
):
    try:
        return await search_product_description(query)
    except Exception:
        return ''
