import asyncio
import time
from os import environ

import pytest
from dotenv import load_dotenv

from asyncrepo.exceptions import ItemNotFound
from asyncrepo.repositories.github.repos import Repos
from asyncrepo.repository import Item, Page, Repository

load_dotenv()

GITHUB_TOKEN = environ['GITHUB_TOKEN']
GITHUB_USER = "nottheswimmer"
KNOWN_REPOSITORIES = ["nottheswimmer/pytago",
                      "nottheswimmer/asyncrepo",
                      "nottheswimmer/excalimaid",
                      "nottheswimmer/i_love_hello_world",
                      "nottheswimmer/podcastsync",
                      "nottheswimmer/arbitrary-dateparser"]


def get_repository():
    return Repos(GITHUB_TOKEN, user=GITHUB_USER)


def test_repository():
    assert isinstance(get_repository(), Repository)


@pytest.mark.asyncio
async def test_list():
    total_pages = total_items = 0
    identifiers = set()
    async for page in get_repository().list_pages():
        total_pages += 1
        assert isinstance(page, Page)
        for item in page.items:
            assert isinstance(item, Item)
            total_items += 1
            assert item.id not in identifiers
            assert GITHUB_USER == item.document['owner']['login']
            identifiers.add(item.id)
    assert total_pages > 0
    assert total_items > 0
    for known_repository in KNOWN_REPOSITORIES:
        assert known_repository in identifiers


@pytest.mark.asyncio
async def test_get_when_identifier_exists():
    item = await get_repository().get(KNOWN_REPOSITORIES[0])
    assert isinstance(item, Item)
    assert item.id == KNOWN_REPOSITORIES[0]


@pytest.mark.asyncio
async def test_get_when_identifier_does_not_exist():
    with pytest.raises(ItemNotFound):
        await get_repository().get(f'{GITHUB_USER}/non-existent')


@pytest.mark.asyncio
async def test_get_async_is_faster():
    """
    TODO: Replace this test with something less fragile. It's important to have something
      like this that can be used to test concurrency, but there are better ways to do this
      than assuming the concurrent approach will always be faster.
    """
    n_repos = len(KNOWN_REPOSITORIES)

    # First, we'll get n_repos using asyncio.gather() and time that.
    start_async = time.time()
    repository = get_repository()
    gh_repos = await asyncio.gather(*[repository.get(repo) for repo in KNOWN_REPOSITORIES])
    elapsed_async = time.time() - start_async
    average_async = elapsed_async / n_repos

    # Then, we'll get n_repos sequentially and time that. Use a new repository to avoid caching.
    repository = get_repository()
    start_sync = time.time()
    gh_repos_2 = []
    for known_repository in KNOWN_REPOSITORIES:
        gh_repos_2.append(await repository.get(known_repository))
    elapsed_sync = time.time() - start_sync
    average_sync = elapsed_sync / n_repos

    # Sanity check / something to look at during debugging.
    assert len(gh_repos) == len(gh_repos_2)

    # Finally, we'll check that the asyncio.gather() is at least faster than the sequential version.
    n_times_faster = average_sync / average_async
    assert n_times_faster > 1
