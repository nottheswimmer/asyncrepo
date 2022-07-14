import pytest
import uuid

from asyncrepo.repository import Page, Item, Repository
from asyncrepo.exceptions import ItemNotFoundError
from asyncrepo.repositories.aws.buckets import Buckets


def get_repository():
    return Buckets()


@pytest.mark.asyncio
async def test_repository():
    assert isinstance(get_repository(), Repository)


@pytest.mark.asyncio
async def test_list_page():
    total_pages = total_buckets = 0
    async_repo_seen = False
    async for page in get_repository().list_pages():
        assert isinstance(page, Page)
        total_pages += 1
        for item in page:
            assert isinstance(item, Item)
            total_buckets += 1
            if item.identifier == "asyncrepo":
                async_repo_seen = True
    assert total_pages == 1  # This is a single page repository
    assert total_buckets > 0
    assert async_repo_seen


@pytest.mark.asyncio
async def test_get():
    assert (await get_repository().get("asyncrepo")).identifier == "asyncrepo"


@pytest.mark.asyncio
async def test_get_not_found():
    with pytest.raises(ItemNotFoundError):
        await get_repository().get(uuid.uuid4().hex)
