from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional, Callable, Awaitable, Iterator, TypeVar

from asyncrepo.utils.text import matches


class Repository(ABC):
    """
    A repository can search, list, and retrieve items from some source.
    """

    async def __aiter__(self) -> AsyncGenerator['Item', None]:
        async for item in self.list():
            yield item

    async def list(self, *args, **kwargs) -> AsyncGenerator['Item', None]:
        async for page in self.list_pages(*args, **kwargs):
            for item in page:
                yield item

    async def list_pages(self, *args, **kwargs) -> AsyncGenerator['Page', None]:
        page = await self.list_page(*args, **kwargs)
        while page:
            yield page
            page = await page.next_page()

    async def search(self, query: str, *args, **kwargs) -> AsyncGenerator['Item', None]:
        async for page in self.search_pages(query, *args, **kwargs):
            for item in page:
                yield item

    async def search_pages(self, query: str, *args, **kwargs) -> AsyncGenerator['Page', None]:
        page = await self.search_page(query, *args, **kwargs)
        while page is not None:
            yield page
            page = await page.next_page()

    async def search_page(self, query: str, *args, **kwargs) -> 'Page':
        """
        Search for items in the repository.

        This is meant to be overridden by the repository, but a default implementation is provided that uses the
        list_page method for asyncrepo for cases where no repository-specific search is available.
        """
        return await self._list_search(query, *args, **kwargs)

    @abstractmethod
    async def list_page(self, *args, **kwargs) -> 'Page':
        raise NotImplementedError()

    @abstractmethod
    async def get(self, id: str) -> 'Item':
        raise NotImplementedError()

    async def _list_search(self, query: str, *args, **kwargs) -> 'Page':
        page = await self.list_page(*args, **kwargs)
        return await page._list_search(query)


RepositoryImplementation = TypeVar('RepositoryImplementation', bound=Repository)


class Page:
    def __init__(self, repository: RepositoryImplementation, items: list['Item'],
                 next_page_fn: Optional[Callable[[], Awaitable['Page']]] = None):
        self.repository = repository
        self.items = items
        self._next_page_fn = next_page_fn

    def __iter__(self) -> Iterator['Item']:
        return iter(self.items)

    def __getitem__(self, index: int) -> 'Item':
        return self.items[index]

    def __len__(self) -> int:
        return len(self.items)

    async def next_page(self) -> Optional['Page']:
        if self._next_page_fn is None:
            return None
        return await self._next_page_fn()

    async def _list_search(self, query: str) -> 'Page':
        self.items = [item for item in self.items if item.matches(query)]
        if self._next_page_fn is not None:
            old_next_page_fn = self._next_page_fn

            async def _next_page_fn() -> 'Page':
                page = await old_next_page_fn()
                return await page._list_search(query)

            self._next_page_fn = _next_page_fn
        return self


class Item:
    def __init__(self, repository: RepositoryImplementation, id: str, document: dict):
        self.repository = repository
        self.id = id
        self.document = document

    def matches(self, query: str) -> bool:
        return matches(query, self.document)
