import ssl

import certifi
import aiohttp


class HttpClient(aiohttp.ClientSession):
    def __init__(self, *args, add_ssl_context=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.__ssl_context = ssl.create_default_context(cafile=certifi.where()) if add_ssl_context else None

    async def _request(self, *args, **kwargs):
        if self.__ssl_context and "ssl_context" not in kwargs:
            kwargs["ssl_context"] = self.__ssl_context
        return await super()._request(*args, **kwargs)
