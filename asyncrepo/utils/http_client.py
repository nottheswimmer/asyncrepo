import ssl
import warnings

import certifi
import aiohttp

warnings.filterwarnings("ignore", message="Inheritance class HttpClient from ClientSession is discouraged")


class HttpClient(aiohttp.ClientSession):
    def __init__(self, *args, add_ssl_context=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.__ssl_context = ssl.create_default_context(cafile=certifi.where()) if add_ssl_context else None

    async def _request(self, *args, **kwargs):
        if self.__ssl_context and "ssl" not in kwargs:
            kwargs["ssl"] = self.__ssl_context
        return await super()._request(*args, **kwargs)
