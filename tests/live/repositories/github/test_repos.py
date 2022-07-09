from os import environ
from unittest import IsolatedAsyncioTestCase

from dotenv import load_dotenv

from asyncrepo.exceptions import ItemNotFoundError
from asyncrepo.repositories.github.repos import Repos
from asyncrepo.repository import Item, Page, Repository

load_dotenv()


class TestRepos(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.user = environ.get('GITHUB_USER')
        self.known_repository = environ.get('GITHUB_REPOSITORY')
        self.repository = Repos(environ['GITHUB_TOKEN'], user=self.user)

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
                self.assertEqual(self.user, item.raw['owner']['login'])
                identifiers.add(item.identifier)
        self.assertGreater(total_pages, 0)
        self.assertGreater(total_items, 0)
        self.assertIn(self.known_repository, identifiers)

    async def test_get_when_identifier_exists(self):
        item = await self.repository.get(self.known_repository)
        self.assertIsInstance(item, Item)
        self.assertEqual(item.identifier, self.known_repository)

    async def test_get_when_identifier_does_not_exist(self):
        with self.assertRaises(ItemNotFoundError):
            await self.repository.get(f'{self.user}/non-existent')
