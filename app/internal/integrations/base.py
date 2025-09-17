import json
from aiohttp import ClientSession, ClientTimeout
from time import time
from asyncio import sleep


class ClientException(Exception):
    def __init__(
        self,
        *,
        payload: dict | None = None,
        url: str | None = None,
        response: dict | None = None,
        msg: str | None = None,
    ):
        self.url = url
        self.payload = payload
        self.response = response
        self.msg = msg
        super().__init__(msg)

    def __str__(self):
        _str = f'\nmsg: {self.msg}' if self.msg else ''
        _str += f'\nurl: {self.url}' if self.url else ''
        _str += f'\npayload: {json.dumps(self.payload)}' if self.payload else ''
        _str += f'\nresponse: {self.response}' if self.response else ''
        return _str


class BaseClient:
    def __init__(self, min_interval: float = 0.1):
        self.__last_request_time: float = 0
        self._min_interval = min_interval

    async def _rate_limit(self):
        """Aplica rate limiting para asegurar 1 petición por segundo"""
        current_time = time()
        time_since_last_request = current_time - self.__last_request_time

        if time_since_last_request < self._min_interval:
            sleep_time = self._min_interval - time_since_last_request
            await sleep(sleep_time)

    def build_url(self, host: str, path: str, params: list[str] | None = None, query_params: dict | None = None):
        url = f'{host}{path}'
        if params:
            url += f'/{"/".join(params)}'
        if query_params:
            url += f'?{"&".join([f"{k}={v}" for k, v in query_params.items()])}'
        return url

        self._last_request_time = time()

    async def request(self, method: str, headers: dict, url: str, payload: dict | None = None, timeout: int = 30):
        if self._min_interval > 0:
            await self._rate_limit()
        client_timeout = ClientTimeout(total=timeout)
        async with ClientSession() as session:
            async with session.request(method, url, headers=headers, json=payload, timeout=client_timeout) as response:
                return await response.json()
