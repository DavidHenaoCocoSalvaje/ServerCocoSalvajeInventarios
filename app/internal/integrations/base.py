import json
import httpx
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

    def __repr__(self):
        return self.__str__()


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
        if self._min_interval > 0:
            await self._rate_limit()

        if params:
            url += f'/{"/".join(params)}'

        timeout_config = httpx.Timeout(float(timeout))
        async with httpx.AsyncClient(timeout=timeout_config) as client:
            response = await client.request(
                method, url, params=query_params, headers=headers, json=payload, cookies=cookies
            )
            try:
                return response.json()
            except (ValueError, httpx.DecodingError):
                raise ClientException(
                    payload=payload, url=url, response={'statuc_code': response.status_code, 'content': response.text}
                )
