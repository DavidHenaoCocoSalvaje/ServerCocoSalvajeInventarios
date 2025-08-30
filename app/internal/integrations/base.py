from aiohttp import ClientSession


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
        _str = f'\nurl: {self.url}' if self.url else ''
        _str += f'\npayload: {self.payload}' if self.payload else ''
        _str += f'\nresponse: {self.response}' if self.response else ''
        _str += f'\nmsg: {self.msg}' if self.msg else ''
        return _str


class BaseClient:
    def build_url(self, host: str, path: str, params: list[str] | None = None, query_params: dict | None = None):
        url = f'{host}{path}'
        if params:
            url += f'/{"/".join(params)}'
        if query_params:
            url += f'?{"&".join([f"{k}={v}" for k, v in query_params.items()])}'
        return url

    async def request(
        self,
        method: str,
        headers: dict,
        url: str,
        payload: dict | None = None,
    ):
        async with ClientSession() as session:
            async with session.request(method, url, headers=headers, json=payload) as response:
                return await response.json()
