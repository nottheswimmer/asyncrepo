import pytest

from asyncrepo.repositories.file.csv_rows import CSVRows
from asyncrepo.repository import Item, Page


def get_repository():
    return CSVRows(
        filepath_or_url='https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties-2020.csv',
        identifier=('date', 'county', 'state'),
        page_size=20)


@pytest.mark.asyncio
async def test_can_list_page():
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
        if total_pages == 5:
            break
    assert total_pages == 5
    assert total_items == 5 * 20


@pytest.mark.asyncio
async def test_can_get_item():
    item = await get_repository().get(str(('2020-03-01', 'New York City', 'New York')))
    assert isinstance(item, Item)
    assert item.id == str(('2020-03-01', 'New York City', 'New York'))
    assert item.document == {
        'date': '2020-03-01',
        'county': 'New York City',
        'state': 'New York',
        'cases': '1',
        'deaths': '0',
        'fips': '',
    }


@pytest.mark.asyncio
async def test_can_search():
    total_items = 0
    async for item in get_repository().search("new york city"):
        assert isinstance(item, Item)
        assert item.document['county'] == "New York City"
        total_items += 1
        if total_items == 10:
            break
    assert total_items == 10
