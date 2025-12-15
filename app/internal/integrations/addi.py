if __name__ == '__main__':
    from os.path import abspath
    from sys import path as sys_path

    sys_path.append(abspath('.'))

from app.config import Config
from app.internal.integrations.base import BaseClient
from app.models.pydantic.addi.transaccion import TransactionsResponse


class AddiClient(BaseClient):
    __instance = None
    acces_token: str = ''

    class Paths:
        class transactions:
            root = '/transactions'

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self, host: str = f'https://ally-portal-external-api.addi.com/{Config.addi_api_version}'):
        super().__init__()
        self.host = host

    @property
    def cookies(self):
        return {'addiauth': self.acces_token}

    async def get_access_token(self):
        # Solicitar acces token a servicio de playwrigth que se ejecuta en el container playwright-api en el puerto 8050 -> 'http://localhost:8050/addi/access-token-addi'
        # Al realizar peticiones entre container, se debe usar el puerto INTERNO ya que son peticiones en la red interna.
        host = 'http://playwright-api:8000' if Config.environment in ['production', 'prod'] else 'http://localhost:8050'
        url = f'{host}/addi/access-token-addi'
        acces_token = await super().request('GET', {}, url)
        self.acces_token = acces_token

    async def request(
        self,
        method: str,
        headers: dict,
        url: str,
        params: list[str] | None = None,
        query_params: dict | None = None,
        payload: dict | None = None,
        timeout: int = 30,
        cookies: dict | None = None,
    ):
        cookies = cookies or {}
        if cookies and not cookies.get('addiauth', None) or cookies is None:
            cookies = {**cookies, **self.cookies}

        result = await super().request(
            method, headers, url, params, query_params, payload, timeout=timeout, cookies=cookies
        )
        if '401' in result.get('code', ''):
            await self.get_access_token()
            cookies = {**cookies, **self.cookies}
            result = await super().request(
                method, headers, url, params, query_params, payload, timeout=timeout, cookies=cookies
            )
        return result

    async def get_transaccions_by_payment_id(self, payment_id: str) -> TransactionsResponse:
        url = f'{self.host}/{self.Paths.transactions.root}'
        transactions_json = await self.request(
            'GET', {}, url, query_params={'limit': 10, 'offset': 0, 'searchField': payment_id}, cookies=self.cookies
        )
        return TransactionsResponse(**transactions_json)


if __name__ == '__main__':
    from asyncio import run

    async def main():
        addi_client = AddiClient()
        await addi_client.get_access_token()
        transacions_response = await addi_client.get_transaccions_by_payment_id('rQUeUgW0WQfUNjLLHPCpfLqyM')
        print(transacions_response)

    run(main())
