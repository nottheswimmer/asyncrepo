from asyncrepo.exceptions import ItemNotFoundError
from asyncrepo.repository import Repository, Page, Item
from asyncrepo.utils.resource_streamer import ResourceStreamer

INDEX = object()


class CSVRows(Repository):
    """
    CSV rows for a specified CSV (filepath or URL)
    """

    def __init__(self, filepath_or_url: str, identifier=INDEX, page_size: int = 20, **csv_reader_kwargs):
        self.filepath_or_url = filepath_or_url
        self.streamer = ResourceStreamer(filepath_or_url)
        self.csv_reader_kwargs = csv_reader_kwargs
        self.page_size = page_size
        self.identifier = identifier

    async def list_page(self, *args, _stream=None, _index=0, **kwargs) -> Page:
        """
        List rows for the CSV
        """
        if _stream is None:
            _stream = self.streamer.stream_csv(**self.csv_reader_kwargs)
        rows = []
        async for row in _stream:
            rows.append(Item(self, self._row_identifier(row, _index), row))
            _index += 1
            if len(rows) == self.page_size:
                break
        next_page_fn = None
        if len(rows) == self.page_size:
            async def next_page_fn() -> Page:
                return await self.list_page(*args, _stream=_stream, _index=_index, **kwargs)
        return Page(self, rows, next_page_fn)

    async def get(self, identifier: str) -> Item:
        """
        Get a row by identifier
        """
        identifier = str(identifier)
        index = 0
        async for page in self.list_pages():
            for item in page:
                if item.identifier == identifier:
                    return item
                index += 1
        raise ItemNotFoundError(identifier)

    def _row_identifier(self, row: dict, index: int) -> str:
        if self.identifier is INDEX:
            return str(index)
        if isinstance(self.identifier, str):
            return row[self.identifier]
        if isinstance(self.identifier, tuple):
            return str(tuple(str(index) if key is INDEX else row[key] for key in self.identifier))
        raise ValueError("Invalid identifier")
