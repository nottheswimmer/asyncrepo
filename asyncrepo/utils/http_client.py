import asyncio
import ssl
import warnings

import certifi
import aiohttp

warnings.filterwarnings("ignore", message="Inheritance class HttpClient from ClientSession is discouraged")
warnings.filterwarnings("ignore", message="Inheritance class BasicAuthHttpClient from ClientSession is discouraged")


class HttpClient(aiohttp.ClientSession):
    def __init__(self, *args, add_ssl_context=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.__ssl_context = ssl.create_default_context(cafile=certifi.where()) if add_ssl_context else None

    async def _request(self, *args, **kwargs):
        if self.__ssl_context and not kwargs.get("ssl"):
            kwargs["ssl"] = self.__ssl_context
        return await super()._request(*args, **kwargs)


class BasicAuthHttpClient(HttpClient):
    def __init__(self, base_url, username, password, *args, **kwargs):
        super().__init__(base_url, *args, **kwargs)
        self.__auth = None
        self.__username = username
        self.__password = password
        self._ensure_auth_lock = asyncio.Lock()

    async def _ensure_auth(self):
        async with self._ensure_auth_lock:
            if self.__auth is None:
                self.__auth = aiohttp.BasicAuth(self.__username, self.__password)

    async def _request(self, *args, **kwargs):
        await self._ensure_auth()
        if not kwargs.get("auth"):
            await self._ensure_auth()
            kwargs["auth"] = self.__auth
        return await super()._request(*args, **kwargs)
