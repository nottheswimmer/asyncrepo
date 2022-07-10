import warnings
from typing import Optional

from asyncrepo.exceptions import ItemNotFoundError
from asyncrepo.utils.http_client import BasicAuthHttpClient

warnings.filterwarnings("ignore", message="Inheritance class JiraClient from ClientSession is discouraged")


class JiraClient(BasicAuthHttpClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def get_issue(self, issue_id_or_key: str) -> dict:
        async with self.get(f"/rest/api/latest/issue/{issue_id_or_key}") as response:
            if response.status == 404:
                raise ItemNotFoundError(issue_id_or_key)
            response.raise_for_status()
            return await response.json()

    async def search(self, query: str = '', max_results: int = 100,
                     start_at: int = 0,
                     validate_query: str = 'none') -> dict:
        params = {
            'jql': query,
            'startAt': start_at,
            'maxResults': max_results,
            'validateQuery': validate_query,
        }
        async with self.get('/rest/api/latest/search', params=params) as response:
            response.raise_for_status()
            data = await response.json()
            return data