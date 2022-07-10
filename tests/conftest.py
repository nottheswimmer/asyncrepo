import asyncio

import pytest


@pytest.fixture(autouse=True)
async def fixture():
    yield
    # (Not so) graceful shutdown
    # https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
    await asyncio.sleep(0.25)
