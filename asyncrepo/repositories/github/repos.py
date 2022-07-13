import asyncio
from typing import Optional

from github import UnknownObjectException
from github.PaginatedList import PaginatedList
from github.Repository import Repository as GithubRepository

from asyncrepo.exceptions import ItemNotFoundError
from asyncrepo.repository import Repository, Page, Item
from asyncrepo.utils.github_client import GithubClient


class Repos(Repository):
    """
    Repos for a specified user or organization from the GitHub API. If no user or organization is specified,
    the authenticated user's asyncrepo will be returned.
    """

    def __init__(self, login_or_token: str, /, user: Optional[str] = None, org: Optional[str] = None,
                 github_kwargs: Optional[dict] = None):
        """
        Initialize a new Repositories repository for the specified user or organization.
        """
        super().__init__()
        self._client = GithubClient(login_or_token, **(github_kwargs or {}))

        if user and org:
            raise ValueError('Cannot specify both user and org')

        self._user_or_org = self._user = self._user_login = self._org = self._org_name = None
        self._list_kwargs = {}
        if user:
            self._user_login = user
        elif org:
            self._org_name = org
            self._list_kwargs['affiliation'] = 'owner'

        self._ensure_user_or_org_lock = asyncio.Lock()

    async def _ensure_user_or_org(self) -> None:
        async with self._ensure_user_or_org_lock:
            if self._user_or_org is None:
                if self._user_login is not None:
                    self._user_or_org = self._user = await self._client.get_user(self._user_login)
                elif self._org_name is not None:
                    self._user_or_org = self._org = await self._client.get_organization(self._org_name)
                else:
                    # Default to the authenticated user
                    self._user_or_org = self._user = await self._client.get_user()

    async def list_page(self, *args, **kwargs) -> Page:
        """
        List the asyncrepo for the user or organization.
        """
        await self._ensure_user_or_org()
        paginated_list = self._user_or_org.get_repos(*args, **kwargs, **self._list_kwargs)
        return await self._page_from_paginated_list(paginated_list)

    async def get(self, identifier: str) -> Item:
        """
        Get the repository with the specified identifier. This will return any repository the client has access to,
        regardless of whether it's associated with the user or organization.
        """
        await self._ensure_user_or_org()
        try:
            repo = await self._client.get_repo(identifier)
        except UnknownObjectException:
            raise ItemNotFoundError(identifier)
        return await self._item_from_github_repo(repo)

    async def search_page(self, query: str, *args, **kwargs) -> 'Page':
        """
        Search for asyncrepo matching the specified query for the user or organization.
        There is no guarantee that a specially constructed query could not cause this to
        return results for asyncrepo not associated with the user or organization.
        """
        await self._ensure_user_or_org()
        qualifiers = {}
        if self._user is not None:
            qualifiers['user'] = self._user.login
        if self._org is not None:
            qualifiers['org'] = self._org.name
        paginated_list = self._client.search_repositories(query, *args, **kwargs, **qualifiers)
        return await self._page_from_paginated_list(paginated_list)

    async def _page_from_paginated_list(self, paginated_list: PaginatedList, page=0, seen=0) -> Page:
        next_page = None
        items = await asyncio.gather(*[self._item_from_github_repo(repo) for repo in await paginated_list.get_page_async(page)])
        seen += len(items)
        if seen < await paginated_list.total_count_async():
            async def next_page() -> 'Page':
                return await self._page_from_paginated_list(paginated_list, page=page + 1, seen=seen)
        return Page(self, items, next_page)

    async def _item_from_github_repo(self, repo: GithubRepository) -> Item:
        return Item(self, repo.full_name, await repo.raw_data_async())

    def _item_from_raw(self, raw: dict) -> Item:
        return Item(self, raw['full_name'], raw)
