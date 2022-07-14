import asyncio
import os
from math import ceil
from typing import NamedTuple

import pytest
from dotenv import load_dotenv

from asyncrepo.exceptions import ItemNotFound
from asyncrepo.repositories.confluence.pages import Pages
from asyncrepo.repository import Item, Page, Repository

load_dotenv()

CONFLUENCE_USERNAME = os.environ['CONFLUENCE_USERNAME']
CONFLUENCE_API_TOKEN = os.environ['CONFLUENCE_API_TOKEN']
CONFLUENCE_BASE_URL = os.environ['CONFLUENCE_BASE_URL']
CONFLUENCE_BASE_PATH = os.environ.get('CONFLUENCE_BASE_PATH', '/wiki')

tc = NamedTuple('TestContent', [('id', int), ('title', str), ('search_term', str)])
KNOWN_PAGES = [
    tc(id=262363, title="How-to article", search_term="How-to article"),
    tc(id=229450, title="Decision", search_term="Decision"),
    tc(id=229457, title="Product requirements", search_term="Product requirements"),
    tc(id=262372, title="Meeting notes", search_term="Meeting notes"),
    tc(id=229441, title="Meeting notes", search_term="Meeting notes"),
    tc(id=262381, title="Master project documentation", search_term="Master project documentation"),
    tc(id=196610, title="Test page with hello world in description", search_term="hello world"),
    tc(id=229603, title="Test page with lorem ipsum description", search_term="dolor sit amet"),
    tc(id=262351, title="AsyncRepo", search_term="AsyncRepo"),
    tc(id=229443, title="Overview", search_term="Overview"),
    tc(id=229442, title="Sample Pages", search_term="Sample Pages"),
]
EXTRA_UNLISTED_PAGES = 1
TOTAL_PAGES = len(KNOWN_PAGES) + EXTRA_UNLISTED_PAGES


def assert_item_matches_test_page(item: Item, test_page: tc):
    assert isinstance(item, Item)
    assert item.id == str(test_page.id)
    assert item.document['id'] == str(test_page.id)
    assert item.document['title'] == test_page.title


def get_repository():
    return Pages(CONFLUENCE_BASE_URL, CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN, base_path=CONFLUENCE_BASE_PATH)


def test_repository():
    assert isinstance(get_repository(), Repository)


@pytest.mark.asyncio
async def test_list():
    total_pages = total_items = 0
    identifiers = set()
    # Paginate by 2 items per page to ensure pagination works
    async for page in get_repository().list_pages(limit=2):
        total_pages += 1
        assert isinstance(page, Page)
        for item in page.items:
            assert isinstance(item, Item)
            total_items += 1
            assert item.id not in identifiers
            assert item.id == item.document['id']
            identifiers.add(item.id)
    assert total_items == TOTAL_PAGES
    assert total_pages == ceil(TOTAL_PAGES / 2)
    for known_page in KNOWN_PAGES:
        assert str(known_page.id) in identifiers


@pytest.mark.asyncio
async def test_get_when_identifier_id_exists():
    item = await get_repository().get(str(KNOWN_PAGES[0].id))
    assert_item_matches_test_page(item, KNOWN_PAGES[0])


@pytest.mark.asyncio
async def test_get_when_identifier_does_not_exist():
    with pytest.raises(ItemNotFound):
        await get_repository().get('1333337')


@pytest.mark.asyncio
@pytest.mark.flaky(reruns=5)
async def test_search():
    repository = get_repository()

    async def assert_test_item_can_be_searched(test_item):
        seen = {}
        async for page in repository.search_pages(test_item.search_term):
            assert isinstance(page, Page)
            for item in page.items:
                seen[item.id] = item

        # str(test_item.id) in seen: Fails
        # str(test_item.id) in list(seen.keys()): Works?
        # Whatever...
        assert str(test_item.id) in list(seen.keys())
        assert_item_matches_test_page(seen[str(test_item.id)], test_item)

    await asyncio.gather(*[assert_test_item_can_be_searched(t) for t in KNOWN_PAGES])
