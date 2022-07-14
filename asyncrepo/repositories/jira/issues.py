import asyncio

from asyncrepo.repository import Repository, Page, Item
from asyncrepo.utils.jira_client import JiraClient


class Issues(Repository):
    def __init__(self, base_url: str, username: str, password: str):
        self.jira_client = None
        self._base_url = base_url
        self._username = username
        self._password = password
        self._ensure_jira_client_lock = asyncio.Lock()

    async def _ensure_jira_client(self):
        async with self._ensure_jira_client_lock:
            if self.jira_client is None:
                self.jira_client = JiraClient(self._base_url, self._username, self._password)

    async def get(self, id: str) -> Item:
        await self._ensure_jira_client()
        data = await self.jira_client.get_issue(id)
        return Item(self, data['id'], data)

    async def _search_jql(self, jql: str, current: int = 0, *args, **kwargs) -> Page:
        await self._ensure_jira_client()
        data = await self.jira_client.search(jql, start_at=current, *args, **kwargs)
        items = [Item(self, item['id'], item) for item in data['issues']]
        next_page_fn = None
        current += len(items)
        if data['total'] > current:
            async def next_page_fn() -> Page:
                return await self._search_jql(jql, current, *args, **kwargs)
        return Page(self, items, next_page_fn)

    async def list_page(self, *args, **kwargs) -> Page:
        return await self._search_jql('order by created DESC', *args, **kwargs)

    async def search_page(self, query: str, *args, **kwargs) -> Page:
        query = query.replace('"', '\\"')
        return await self._search_jql(f'text ~ "{query}" order by created DESC', *args, **kwargs)
