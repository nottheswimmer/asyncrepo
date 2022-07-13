from pathlib import Path

import pytest

from asyncrepo.utils.resource_streamer import ResourceStreamer

TIMELESS_URLS = [
    ("https://www.mcspotlight.org/index.shtml", 7426)
]

CSV_URLS = [
    "https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties-2020.csv",
]


def get_test_data_dir():
    path = Path(__file__)
    prev_path = None
    while path != prev_path and not (path / "test_data").exists():
        prev_path = path
        path = path.parent
    return path / "test_data"


test_data = get_test_data_dir()

FILES = [
    ((test_data / "mcsplotlight.html").as_posix(), 7426),
]

CSV_FILES = [
    (test_data / "us-counties-2020.csv").as_posix()
]


@pytest.mark.asyncio
@pytest.mark.parametrize("url,size", TIMELESS_URLS)
async def test_resource_streamer_can_stream_url(url: str, size: int):
    streamer = ResourceStreamer(url)
    actual_size = 0
    async for line in streamer.stream():
        assert isinstance(line, str)
        actual_size += len(line)
    assert actual_size == size


@pytest.mark.asyncio
@pytest.mark.parametrize("url,size", TIMELESS_URLS)
async def test_resource_streamer_can_stream_url_chunked(url: str, size: int):
    streamer = ResourceStreamer(url, size=10)
    actual_size = 0
    async for line in streamer.stream():
        assert isinstance(line, str)
        assert len(line) <= 10
        actual_size += len(line)
    assert actual_size == size


@pytest.mark.asyncio
@pytest.mark.parametrize("filepath,size", FILES)
async def test_resource_streamer_can_stream_file(filepath: str, size: int):
    streamer = ResourceStreamer(filepath)
    actual_size = 0
    async for line in streamer.stream():
        assert isinstance(line, str)
        actual_size += len(line)
    assert actual_size == size


@pytest.mark.asyncio
@pytest.mark.parametrize("filepath,size", FILES)
async def test_resource_streamer_can_stream_file_chunked(filepath: str, size: int):
    streamer = ResourceStreamer(filepath, size=10)
    actual_size = 0
    async for line in streamer.stream():
        assert isinstance(line, str)
        assert len(line) <= 10
        actual_size += len(line)
    assert actual_size == size


@pytest.mark.asyncio
@pytest.mark.parametrize("url", CSV_URLS)
async def test_resource_streamer_can_stream_csv_url(url: str):
    streamer = ResourceStreamer(url)
    rows = 0
    async for row in streamer.stream_csv():
        rows += 1
        assert isinstance(row, dict)
        for key, value in row.items():
            assert isinstance(key, str)
            assert isinstance(value, str)
        if rows == 10:
            break
    assert rows == 10


@pytest.mark.asyncio
@pytest.mark.parametrize("filepath", CSV_FILES)
async def test_resource_streamer_can_stream_csv_file(filepath: str):
    streamer = ResourceStreamer(filepath)
    rows = 0
    async for row in streamer.stream_csv():
        rows += 1
        assert isinstance(row, dict)
        for key, value in row.items():
            assert isinstance(key, str)
            assert isinstance(value, str)
    assert rows > 0
