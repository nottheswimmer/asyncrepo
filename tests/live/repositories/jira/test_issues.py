import asyncio
import os
from math import ceil
from typing import NamedTuple

import pytest
from dotenv import load_dotenv

from asyncrepo.exceptions import ItemNotFoundError
from asyncrepo.repositories.jira.issues import Issues
from asyncrepo.repository import Item, Page, Repository

load_dotenv()

JIRA_USERNAME = os.environ['JIRA_USERNAME']
JIRA_API_TOKEN = os.environ['JIRA_API_TOKEN']
JIRA_BASE_URL = os.environ['JIRA_BASE_URL']

ti = NamedTuple('TestIssue', [('id', int), ('key', str), ('summary', str), ('search_term', str)])
KNOWN_ISSUES = [
    ti(id=10000, key='AS-1', summary='Test Story with hello world in description', search_term='hello world'),
    ti(id=10001, key='AS-2', summary='Test Task with no description', search_term='Test Task'),
    ti(id=10002, key='AS-3', summary='Test Bug with no description', search_term='Test Bug'),
    ti(id=10003, key='AS-4', summary='Test Epic with no description', search_term='Test Epic'),
    ti(id=10004, key='AS-5', summary='Test Story with lorem ipsum description', search_term='dolor sit amet'),
]


def assert_item_matches_test_issue(item: Item, test_issue: ti):
    assert isinstance(item, Item)
    assert item.identifier == str(test_issue.id)
    assert item.raw['id'] == str(test_issue.id)
    assert item.raw['key'] == test_issue.key
    assert item.raw['fields']['summary'] == test_issue.summary


def get_repository():
    return Issues(JIRA_BASE_URL, JIRA_USERNAME, JIRA_API_TOKEN)


def test_repository():
    assert isinstance(get_repository(), Repository)


@pytest.mark.asyncio
async def test_list():
    total_pages = total_items = 0
    identifiers = set()
    # Paginate by 2 items per page to ensure pagination works
    async for page in get_repository().list_pages(max_results=2):
        total_pages += 1
        assert isinstance(page, Page)
        for item in page.items:
            assert isinstance(item, Item)
            total_items += 1
            assert item.identifier not in identifiers
            assert item.identifier == item.raw['id']
            identifiers.add(item.identifier)
    assert total_pages == ceil(len(KNOWN_ISSUES) / 2)
    assert total_items == len(KNOWN_ISSUES)
    for known_issue in KNOWN_ISSUES:
        assert str(known_issue.id) in identifiers


@pytest.mark.asyncio
async def test_get_when_identifier_id_exists():
    item = await get_repository().get(str(KNOWN_ISSUES[0].id))
    assert_item_matches_test_issue(item, KNOWN_ISSUES[0])


@pytest.mark.asyncio
async def test_get_when_identifier_key_exists():
    item = await get_repository().get(KNOWN_ISSUES[0].key)
    assert_item_matches_test_issue(item, KNOWN_ISSUES[0])


@pytest.mark.asyncio
async def test_get_when_identifier_does_not_exist():
    with pytest.raises(ItemNotFoundError):
        await get_repository().get('AS-0')


@pytest.mark.asyncio
async def test_search():
    repository = get_repository()

    async def assert_test_item_can_be_searched(test_item):
        total_pages = total_items = 0
        async for page in repository.search_pages(test_item.search_term):
            total_pages += 1
            assert isinstance(page, Page)
            for item in page.items:
                total_items += 1
                assert_item_matches_test_issue(item, test_item)
        # Each search term was chosen to match exactly one issue
        assert total_pages == 1
        assert total_items == 1

    await asyncio.gather(*[assert_test_item_can_be_searched(test_item) for test_item in KNOWN_ISSUES])
