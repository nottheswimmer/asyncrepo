import asyncio
from typing import Optional

from asyncrepo.repository import Repository, Page, Item
from asyncrepo.utils.confluence_client import ConfluenceClient


class _Content(Repository):
    def __init__(self, base_url: str, username: str, password: str, base_path: str = "/wiki",
                 _type: Optional[str] = None, _space: Optional[str] = None):
        super().__init__()
        self.confluence_client = None
        self._base_url = base_url
        self._base_path = base_path
        self._username = username
        self._password = password
        self._type = _type
        self._space = _space
        self._ensure_confluence_client_lock = asyncio.Lock()
        prefix_parts = []
        if _type is not None:
            prefix_parts.append(f"type={_type}")
        if _space is not None:
            s = _space.replace('"', '\\"')
            prefix_parts.append(f"space={s}")
        self._start_clause = ' AND '.join(prefix_parts)

    async def _ensure_confluence_client(self):
        async with self._ensure_confluence_client_lock:
            if self.confluence_client is None:
                self.confluence_client = ConfluenceClient(
                    base_url=self._base_url, base_path=self._base_path,
                    username=self._username, password=self._password)

    async def get(self, identifier: str) -> Item:
        await self._ensure_confluence_client()
        data = await self.confluence_client.get_content(identifier)
        return Item(self, data['id'], data)

    async def _search_cql(self, cql: str, current: int = 0, **kwargs) -> Page:
        await self._ensure_confluence_client()
        data = await self.confluence_client.search(cql, start=current, **kwargs)
        items = [Item(self, item['id'], item) for item in data['results']]
        next_page_fn = None
        current += len(items)
        next_link = data.get('_links', {}).get('next')
        if next_link is not None:
            async def next_page_fn() -> Page:
                kwargs['next_link'] = next_link
                return await self._search_cql(cql, current, **kwargs)
        return Page(self, items, next_page_fn)

    async def list_page(self, *args, **kwargs) -> Page:
        return await self._search_cql(self._prefix_cql('order by created DESC'), *args, **kwargs)

    async def search_page(self, query: str, *args, **kwargs) -> Page:
        query = query.replace('"', '\\"')
        return await self._search_cql(self._prefix_cql(f'text ~ "{query}" order by created DESC'), *args, **kwargs)

    def _prefix_cql(self, cql):
        if not self._start_clause:
            return cql
        if cql.startswith('order by'):
            return f"{self._start_clause} {cql}"
        return f"{self._start_clause} AND {cql}"
