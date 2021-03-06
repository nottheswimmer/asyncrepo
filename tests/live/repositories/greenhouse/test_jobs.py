import pytest

from asyncrepo.exceptions import ItemNotFound
from asyncrepo.repositories.greenhouse.jobs import Jobs
from asyncrepo.repository import Item, Page, Repository


def get_repository():
    return Jobs(board_token='insider')


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
            identifiers.add(item.id)
    assert total_pages == 1  # Greenhouse only has one page
    assert total_items > 0


@pytest.mark.asyncio
async def test_get_when_identifier_exists():
    identifier = None
    async for page in get_repository().list_pages():
        for item in page.items:
            identifier = item.id
            break

    item = await get_repository().get(identifier)
    assert isinstance(item, Item)
    assert item.id == identifier


@pytest.mark.asyncio
async def test_get_when_identifier_does_not_exist():
    with pytest.raises(ItemNotFound):
        await get_repository().get('fake-job-id')
