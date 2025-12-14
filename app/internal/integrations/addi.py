from playwright.async_api import async_playwright
from asyncio import sleep


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
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto(url='https://aliados.addi.com/')
            await sleep(3)
            input_email = page.locator('input[name="email"]')
            input_password = page.locator('input[name="password"]')
            login_button = page.get_by_role(
                'button', name='Iniciar sesión'
            )  # Name se refiere al texto visible del botón
            await input_email.fill('jose@cocosalvaje.co')
            await input_password.fill('Coco2025*')
            await login_button.click()
            await sleep(3)
            cookies = await context.cookies()
            access_token = next((c.get('value') for c in cookies if c.get('name') == 'addiauth'), None)
            await browser.close()
            self.acces_token = access_token or ''
            return access_token

    async def request(
        self,
        method: str,
        headers: dict,
        url: str,
        payload: dict | None = None,
        timeout: int = 30,
        cookies: dict | None = None,
    ):
        cookies = cookies or {}
        if cookies and not cookies.get('addiauth', None) or cookies is None:
            cookies = {**cookies, **self.cookies}

        result = await super().request(method, headers, url, payload, timeout=timeout, cookies=cookies)
        if '401' in result.get('code', ''):
            await self.get_access_token()
            cookies = {**cookies, **self.cookies}
            result = await super().request(method, headers, url, payload, timeout=timeout, cookies=cookies)
        return result

    async def get_transaccions_by_payment_id(self, payment_id: str) -> TransactionsResponse:
        url = self.build_url(
            self.host, self.Paths.transactions.root, query_params={'limit': 10, 'offset': 0, 'searchField': payment_id}
        )
        transactions_json = await self.request('GET', {}, url, cookies=self.cookies)
        return TransactionsResponse(**transactions_json)


if __name__ == '__main__':
    from asyncio import run

    async def main():
        addi_client = AddiClient()
        # await addi_client.get_access_token()
        transacions_response = await addi_client.get_transaccions_by_payment_id('rQUeUgW0WQfUNjLLHPCpfLqyM')
        print(transacions_response)

    run(main())
