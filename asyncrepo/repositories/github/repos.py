from typing import Optional

from github import Github, UnknownObjectException
from github.PaginatedList import PaginatedList
from github.Repository import Repository as GithubRepository

from asyncrepo.exceptions import ItemNotFoundError
from asyncrepo.repository import Repository, Page, Item


class Repos(Repository):
    """
    Repos for a specified user or organization from the GitHub API. If no user or organization is specified,
    the authenticated user's asyncrepo will be returned.
    """

    def __init__(self, login_or_token: str, /, user: Optional[str] = None, org: Optional[str] = None, **github_kwargs):
        """
        Initialize a new Repositories repository for the specified user or organization.
        """
        super().__init__()
        # TODO: Non-blocking GitHub Client
        self._client = Github(login_or_token, **github_kwargs)

        if user and org:
            raise ValueError('Cannot specify both user and org')

        self._user = self._org = None
        self._list_kwargs = {}
        if user:
            self._user = self._user_or_org = self._client.get_user(user)
        elif org:
            self._org = self._user_or_org = self._client.get_organization(org)
        else:
            self._user = self._user_or_org = self._client.get_user()
            self._list_kwargs['affiliation'] = 'owner'

    async def list_page(self, *args, **kwargs) -> Page:
        """
        List the asyncrepo for the user or organization.
        """
        paginated_list = self._user_or_org.get_repos(*args, **kwargs, **self._list_kwargs)
        return await self._page_from_paginated_list(paginated_list)

    async def get(self, identifier: str) -> Item:
        """
        Get the repository with the specified identifier. This will return any repository the client has access to,
        regardless of whether it's associated with the user or organization.
        """
        try:
            repo = self._client.get_repo(identifier)
        except UnknownObjectException:
            raise ItemNotFoundError(identifier)
        return self._item_from_github_repo(repo)

    async def search_page(self, query: str, *args, **kwargs) -> 'Page':
        """
        Search for asyncrepo matching the specified query for the user or organization.
        There is no guarantee that a specially constructed query could not cause this to
        return results for asyncrepo not associated with the user or organization.
        """
        qualifiers = {}
        if self._user is not None:
            qualifiers['user'] = self._user.login
        if self._org is not None:
            qualifiers['org'] = self._org.name
        paginated_list = self._client.search_repositories(query, *args, **kwargs, **qualifiers)
        return await self._page_from_paginated_list(paginated_list)

    async def _page_from_paginated_list(self, paginated_list: PaginatedList, page=0, seen=0) -> Page:
        next_page = None
        items = [self._item_from_github_repo(repo) for repo in paginated_list.get_page(page)]
        seen += len(items)
        if seen < paginated_list.totalCount:
            async def next_page() -> 'Page':
                return await self._page_from_paginated_list(paginated_list, page=page + 1, seen=seen)
        return Page(self, items, next_page)

    def _item_from_github_repo(self, repo: GithubRepository) -> Item:
        return Item(self, repo.full_name, repo.raw_data)

    def _item_from_raw(self, raw: dict) -> Item:
        return Item(self, raw['full_name'], raw)
