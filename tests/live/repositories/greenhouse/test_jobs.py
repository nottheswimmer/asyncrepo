from unittest import IsolatedAsyncioTestCase

from asyncrepo.exceptions import ItemNotFoundError
from asyncrepo.repositories.greenhouse.jobs import Jobs
from asyncrepo.repository import Item, Page, Repository


class TestJobs(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.repository = Jobs(board_token='insider')

    async def test_repository(self):
        self.assertIsInstance(self.repository, Repository)

    async def test_list(self):
        total_pages = total_items = 0
        identifiers = set()
        async for page in self.repository.list_pages():
            total_pages += 1
            self.assertIsInstance(page, Page)
            for item in page.items:
                self.assertIsInstance(item, Item)
                total_items += 1
                self.assertNotIn(item.identifier, identifiers)
                identifiers.add(item.identifier)
        self.assertEqual(total_pages, 1)  # Greenhouse only has one page
        self.assertGreater(total_items, 0)

    async def test_get_when_identifier_exists(self):
        identifier = None
        async for page in self.repository.list_pages():
            for item in page.items:
                identifier = item.identifier
                break

        item = await self.repository.get(identifier)
        self.assertIsInstance(item, Item)
        self.assertEqual(item.identifier, identifier)

    async def test_get_when_identifier_does_not_exist(self):
        with self.assertRaises(ItemNotFoundError):
            await self.repository.get('133333337')
