import asyncio
import time
from os import environ
from unittest import IsolatedAsyncioTestCase

from dotenv import load_dotenv

from asyncrepo.exceptions import ItemNotFoundError
from asyncrepo.repositories.github.repos import Repos
from asyncrepo.repository import Item, Page, Repository

load_dotenv()


class TestRepos(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.user = "nottheswimmer"
        self.known_repositories = ["nottheswimmer/pytago",
                                   "nottheswimmer/asyncrepo",
                                   "nottheswimmer/excalimaid",
                                   "nottheswimmer/i_love_hello_world",
                                   "nottheswimmer/podcastsync",
                                   "nottheswimmer/arbitrary-dateparser"]
        self.repository = self.get_repository()

    def get_repository(self) -> Repository:
        return Repos(environ['GITHUB_TOKEN'], user=self.user)

    def test_repository(self):
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
        for known_repository in self.known_repositories:
            self.assertIn(known_repository, identifiers)

    async def test_get_when_identifier_exists(self):
        item = await self.repository.get(self.known_repositories[0])
        self.assertIsInstance(item, Item)
        self.assertEqual(item.identifier, self.known_repositories[0])

    async def test_get_when_identifier_does_not_exist(self):
        with self.assertRaises(ItemNotFoundError):
            await self.repository.get(f'{self.user}/non-existent')

    async def test_get_async_is_faster(self):
        """
        TODO: Replace this test with something less fragile. It's important to have something
          like this that can be used to test concurrency, but there are better ways to do this
          than assuming the concurrent approach will always be faster.
        """
        n_repos = len(self.known_repositories)

        # First, we'll get n_repos using asyncio.gather() and time that.
        start_async = time.time()
        gh_repos = await asyncio.gather(*[self.repository.get(repo) for repo in self.known_repositories])
        elapsed_async = time.time() - start_async
        average_async = elapsed_async / n_repos

        # Then, we'll get n_repos sequentially and time that. Use a new repository to avoid caching.
        repository = self.get_repository()
        start_sync = time.time()
        gh_repos_2 = []
        for known_repository in self.known_repositories:
            gh_repos_2.append(await repository.get(known_repository))
        elapsed_sync = time.time() - start_sync
        average_sync = elapsed_sync / n_repos

        # Sanity check / something to look at during debugging.
        self.assertEqual(len(gh_repos), len(gh_repos_2))

        # Finally, we'll check that the asyncio.gather() is at least faster than the sequential version.
        n_times_faster = average_sync / average_async
        self.assertGreater(n_times_faster, 1)
