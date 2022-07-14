import pytest
import uuid

from asyncrepo.repository import Page, Item, Repository
from asyncrepo.exceptions import ItemNotFoundError
from asyncrepo.repositories.aws.s3_objects import S3Objects


def get_repository():
    return S3Objects("asyncrepo")


@pytest.mark.asyncio
async def test_repository():
    assert isinstance(get_repository(), Repository)


@pytest.mark.asyncio
async def test_list_page():
    total_pages = total_buckets = 0
    hello_world_seen = False
    async for page in get_repository().list_pages():
        assert isinstance(page, Page)
        total_pages += 1
        for item in page:
            assert isinstance(item, Item)
            total_buckets += 1
            if item.identifier == "hello_world_1.txt":
                hello_world_seen = True
    assert total_pages >= 1
    assert total_buckets > 0
    assert hello_world_seen


@pytest.mark.asyncio
async def test_get():
    assert (await get_repository().get("hello_world_1.txt")).identifier == "hello_world_1.txt"


@pytest.mark.asyncio
async def test_get_not_found():
    with pytest.raises(ItemNotFoundError):
        await get_repository().get(uuid.uuid4().hex)


@pytest.mark.asyncio
async def test_search_page():
    total_pages = total_buckets = 0
    hello_world_seen = False
    async for page in get_repository().search_pages("hello"):
        assert isinstance(page, Page)
        total_pages += 1
        for item in page:
            assert isinstance(item, Item)
            total_buckets += 1
            if item.identifier == "hello_world_1.txt":
                hello_world_seen = True
    assert total_pages >= 1
    assert total_buckets > 0
    assert hello_world_seen


@pytest.mark.asyncio
async def test_search_page_not_found():
    total_pages = total_buckets = 0
    async for page in get_repository().search_pages("not_found"):
        assert isinstance(page, Page)
        total_pages += 1
        for item in page:
            assert isinstance(item, Item)
            total_buckets += 1
    assert total_pages == 1
    assert total_buckets == 0