from asyncrepo.exceptions import ItemNotFound
from asyncrepo.repository import Repository, Page, Item
from asyncrepo.utils.http_client import HttpClient

_LIST_ENDPOINT = '/v1/boards/{board_token}/jobs'
_ITEM_ENDPOINT = '/v1/boards/{board_token}/jobs/{job_id}'


class Jobs(Repository):
    """
    Jobs for a specified board from the Greenhouse API.
    """

    def __init__(self, board_token: str, base_url: str = "https://api.greenhouse.io/"):
        """
        Initialize a new Jobs repository for the specified board.

        :param board_token: The board token.
        :param base_url: The base URL of the Greenhouse API.
        """
        super().__init__()
        self.board_token = board_token
        self.base_url = base_url

    async def list_page(self, content: bool = True) -> 'Page':
        """
        List jobs for the board.

        https://developers.greenhouse.io/job-board.html#list-jobs

        :param content: Unless disabled, include the full post description, department, and office of each job post.
        """
        params = {'content': str(content).lower()} if content else {}
        async with HttpClient(self.base_url) as client:
            async with client.get(self._list_endpoint(), params=params) as r:
                r.raise_for_status()
                data = await r.json()
                return self._page_from_payload(data)

    async def get(self, job_id: str, questions: bool = False) -> 'Item':
        """
        Get a job by ID.

        https://developers.greenhouse.io/job-board.html#retrieve-a-job

        :param job_id: The job ID.
        :param questions: If enabled, include additional questions fields in the response.
        """
        params = {'questions': str(questions).lower()} if questions else {}
        async with HttpClient(self.base_url) as client:
            async with client.get(self._item_endpoint(job_id), params=params) as r:
                if r.status == 404:
                    raise ItemNotFound(job_id)
                r.raise_for_status()
                data = await r.json()
                return self._item_from_payload(data)

    def _page_from_payload(self, data: dict) -> 'Page':
        return Page(self, [self._item_from_payload(item) for item in data['jobs']], None)

    def _item_from_payload(self, data: dict) -> 'Item':
        return Item(self, str(data['id']), data)

    def _list_endpoint(self) -> str:
        return _LIST_ENDPOINT.format(board_token=self.board_token)

    def _item_endpoint(self, job_id: str) -> str:
        return _ITEM_ENDPOINT.format(board_token=self.board_token, job_id=job_id)
