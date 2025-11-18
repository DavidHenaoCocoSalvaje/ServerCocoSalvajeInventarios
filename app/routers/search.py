from fastapi import APIRouter, Depends, HTTPException, status

from app.internal.integrations.bing import search_bing_copilot
from app.internal.log import factory_logger
from app.routers.auth import validar_access_token


router = APIRouter(
    prefix='/search',
    responses={404: {'description': 'No encontrado'}},
    tags=['Search'],
    dependencies=[Depends(validar_access_token)],
)

log_search = factory_logger('search')


@router.post(
    '/bing',
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(validar_access_token)],
)
async def post_search_bing_copilot(
    query: str,
):
    try:
        return await search_bing_copilot(query)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
