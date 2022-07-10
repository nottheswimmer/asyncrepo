import asyncio
import warnings

from asyncrepo.exceptions import ItemNotFoundError
from asyncrepo.utils.http_client import BasicAuthHttpClient

warnings.filterwarnings("ignore", message="Inheritance class ConfluenceClient from ClientSession is discouraged")


class ConfluenceClient(BasicAuthHttpClient):
    def __init__(self, /, base_path: str = "/wiki", **kwargs):
        base_path = base_path.rstrip('/')
        if not base_path.startswith('/'):
            base_path = '/' + base_path
        self._base_path = base_path
        super().__init__(**kwargs)

    async def get_content(self, content_id_or_key: str) -> dict:
        async with self.get(self._base_path + f"/rest/api/content/{content_id_or_key}") as response:
            if response.status == 404:
                raise ItemNotFoundError(content_id_or_key)
            response.raise_for_status()
            return await response.json()

    async def search(self, query: str = '', limit: int = 100,
                     start: int = 0, **kwargs) -> dict:
        params = {
            'cql': query,
            'start': start,
            'limit': limit,
            'expand': 'space,body.view,body.storage,body.export_view',
        }

        # Confluence uses a cursor to paginate so we'll allow just passing in a next_link from kwargs
        if "next_link" in kwargs:
            url = kwargs["next_link"]
            if not url.lower().startswith("http"):
                url = self._base_path + url
            kwargs.pop("next_link")
            params = {}
        else:
            url = self._base_path + '/rest/api/content/search'

        # Hack: Confluence has a tendency to 500 if there's too much concurrency?
        # I'm just going to throw in a retry system here but this should be abstracted out
        max_tries = 5
        status = -1
        warned = False
        while max_tries > 0:
            try:
                async with self.get(url, params=params) as response:
                    status = response.status
                    response.raise_for_status()
                    return await response.json()
            except Exception as e:
                max_tries -= 1
                if max_tries == 0:
                    raise e
                if not warned:
                    warnings.warn(f"Confluence search resulted in a {status} error. "
                                  f"You may be querying too much at once. "
                                  f"Retrying {max_tries} more times after a short delay.")
                await asyncio.sleep(0.1)
