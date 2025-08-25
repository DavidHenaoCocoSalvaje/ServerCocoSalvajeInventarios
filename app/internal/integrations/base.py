from aiohttp import ClientSession


class BaseClient:
    def __init__(self, host: str, headers: dict | None = None):
        self.host = host
        self._headers = headers.copy() if headers else {}

    @property
    def headers(self):
        return self._headers.copy()

    @headers.setter
    def headers(self, headers: dict):
        self._headers = headers.copy()

    def set_header(self, key: str, value: str):
        self._headers[key] = value

    def update_headers(self, headers: dict):
        self._headers.update(headers)

    def _build_url(self, path: str, params: list[str] | None = None, query_params: dict | None = None):
        url = f'{self.host}{path}'
        if params:
            url += f'/{"/".join(params)}'
        if query_params:
            url += f'?{"&".join([f"{k}={v}" for k, v in query_params.items()])}'
        return url

    async def _request(
        self,
        method: str,
        path: str,
        params: list[str] | None = None,
        query_params: dict | None = None,
        payload: dict | None = None,
    ):
        url = self._build_url(path, params, query_params)

        async with ClientSession() as session:
            async with session.request(method, url, headers=self.headers, json=payload) as response:
                return await response.json()

    async def get(self, path: str, params: list[str] | None = None, query_params: dict | None = None):
        return await self._request('GET', path, params, query_params)

    async def post(
        self, path: str, params: list[str] | None = None, query_params: dict | None = None, payload: dict | None = None
    ):
        return await self._request('POST', path, params, query_params, payload)

    async def put(
        self, path: str, params: list[str] | None = None, query_params: dict | None = None, payload: dict | None = None
    ):
        return await self._request('PUT', path, params, query_params, payload)

    async def patch(
        self, path: str, params: list[str] | None = None, query_params: dict | None = None, payload: dict | None = None
    ):
        return await self._request('PATCH', path, params, query_params, payload)

    async def delete(self, path: str, params: list[str] | None = None, query_params: dict | None = None):
        return await self._request('DELETE', path, params, query_params)

    async def options(self, path: str, params: list[str] | None = None, query_params: dict | None = None):
        return await self._request('OPTIONS', path, params, query_params)
