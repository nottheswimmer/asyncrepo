import asyncio
import time
from os import environ

import pytest
from dotenv import load_dotenv

from asyncrepo.exceptions import ItemNotFoundError
from asyncrepo.repositories.github.repos import Repos
from asyncrepo.repository import Item, Page, Repository
from tests.utils import async_test

load_dotenv()

user = "nottheswimmer"
known_repositories = ["nottheswimmer/pytago",
                      "nottheswimmer/asyncrepo",
                      "nottheswimmer/excalimaid",
                      "nottheswimmer/i_love_hello_world",
                      "nottheswimmer/podcastsync",
                      "nottheswimmer/arbitrary-dateparser"]


def get_repository():
    return Repos(environ['GITHUB_TOKEN'], user=user)


def test_repository():
    assert isinstance(get_repository(), Repository)


@async_test
async def test_list():
    total_pages = total_items = 0
    identifiers = set()
    async for page in get_repository().list_pages():
        total_pages += 1
        assert isinstance(page, Page)
        for item in page.items:
            assert isinstance(item, Item)
            total_items += 1
            assert item.identifier not in identifiers
            assert user == item.raw['owner']['login']
            identifiers.add(item.identifier)
    assert total_pages > 0
    assert total_items > 0
    for known_repository in known_repositories:
        assert known_repository in identifiers


@async_test
async def test_get_when_identifier_exists():
    item = await get_repository().get(known_repositories[0])
    assert isinstance(item, Item)
    assert item.identifier == known_repositories[0]


@async_test
async def test_get_when_identifier_does_not_exist():
    with pytest.raises(ItemNotFoundError):
        await get_repository().get(f'{user}/non-existent')


@async_test
async def test_get_async_is_faster():
    """
    TODO: Replace this test with something less fragile. It's important to have something
      like this that can be used to test concurrency, but there are better ways to do this
      than assuming the concurrent approach will always be faster.
    """
    n_repos = len(known_repositories)

    # First, we'll get n_repos using asyncio.gather() and time that.
    start_async = time.time()
    repository = get_repository()
    gh_repos = await asyncio.gather(*[repository.get(repo) for repo in known_repositories])
    elapsed_async = time.time() - start_async
    average_async = elapsed_async / n_repos

    # Then, we'll get n_repos sequentially and time that. Use a new repository to avoid caching.
    repository = get_repository()
    start_sync = time.time()
    gh_repos_2 = []
    for known_repository in known_repositories:
        gh_repos_2.append(await repository.get(known_repository))
    elapsed_sync = time.time() - start_sync
    average_sync = elapsed_sync / n_repos

    # Sanity check / something to look at during debugging.
    assert len(gh_repos) == len(gh_repos_2)

    # Finally, we'll check that the asyncio.gather() is at least faster than the sequential version.
    n_times_faster = average_sync / average_async
    assert n_times_faster > 1
