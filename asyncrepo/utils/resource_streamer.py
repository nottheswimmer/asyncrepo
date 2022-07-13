import codecs
from pathlib import Path
from typing import Optional

import aiocsv
from aiopath.path import AsyncPath
from anyio import AsyncFile

from asyncrepo.utils.http_client import HttpClient


class ResourceStreamer:
    def __init__(self, filepath_or_url: str, is_file: Optional[bool] = None, size=None):
        self.filepath_or_url = filepath_or_url
        self.is_file = is_file
        self.size = size

    async def stream(self):
        filepath = None
        if self.is_file in [None, True]:
            filepath = await self._resolve_filepath()
        if filepath is not None:
            async for line in self._stream_filepath(filepath):
                yield line
        elif self.is_file in [None, False]:
            async for line in self._stream_url(self.filepath_or_url):
                yield line
        else:
            raise ValueError('Invalid filepath or URL', self.filepath_or_url)

    async def stream_csv(self, **csv_reader_kwargs):
        filepath = None
        if self.is_file in [None, True]:
            filepath = await self._resolve_filepath()
        if filepath is not None:
            async for row in self._stream_csv_filepath(filepath, **csv_reader_kwargs):
                yield row
        elif self.is_file in [None, False]:
            async for row in self._stream_csv_url(self.filepath_or_url, **csv_reader_kwargs):
                yield row
        else:
            raise ValueError('Invalid filepath or URL', self.filepath_or_url)

    async def _resolve_filepath(self):
        try:
            # If you don't do this, AsyncPath will literally kill the entire event loop
            # with an unrecoverable exception when this function gets called with a URL.
            # In fact, I'm not positive there aren't still inputs that can cause such an
            # error.
            friendly_path = Path(self.filepath_or_url)
            if not friendly_path.is_absolute():
                return None
        except ValueError:
            return None

        path = AsyncPath(friendly_path)
        if not await path.exists():
            return None
        if not await path.is_file():
            return None
        return path

    async def _stream_filepath(self, filepath: AsyncPath):
        async with filepath.open('r') as f:
            if self.size is None:
                async for line in f:
                    yield line
            else:
                f: AsyncFile
                while True:
                    line = await f.read(self.size)
                    if not line:
                        break
                    yield line

    async def _stream_url(self, url: str, errors='strict'):
        async with HttpClient() as client:
            async with client.get(url) as r:
                encoding = r.headers.get('Content-Type', '').split('charset=')
                encoding = encoding[1] if len(encoding) > 1 else 'utf-8'
                decoder_factory = codecs.getincrementaldecoder(encoding)

                self.decoder = decoder_factory(errors)

                if not self.size:
                    async for line in r.content.iter_any():
                        yield self.decoder.decode(line, final=False)
                else:
                    async for line in r.content.iter_chunked(self.size):
                        yield self.decoder.decode(line, final=False)
                yield self.decoder.decode(b'', final=True)

    async def _stream_csv_url(self, url: str, **csv_reader_kwargs):
        async with HttpClient() as client:
            async with client.get(url) as r:
                encoding = r.headers.get('Content-Type', '').split('charset=')
                encoding = encoding[1] if len(encoding) > 1 else 'utf-8'
                reader = AsyncTextReaderWrapper(r.content, encoding, errors='strict')
                async for row in aiocsv.AsyncDictReader(reader, **csv_reader_kwargs):
                    yield row


    async def _stream_csv_filepath(self, filepath: AsyncPath, **csv_reader_kwargs):
        async with filepath.open('r') as f:
            async for row in aiocsv.AsyncDictReader(f, **csv_reader_kwargs):
                yield row


class AsyncTextReaderWrapper:
    def __init__(self, obj, encoding, errors="strict"):
        self.obj = obj

        decoder_factory = codecs.getincrementaldecoder(encoding)
        self.decoder = decoder_factory(errors)

    async def read(self, size):
        raw_data = await self.obj.read(size)

        if not raw_data:
            return self.decoder.decode(b"", final=True)

        return self.decoder.decode(raw_data, final=False)
