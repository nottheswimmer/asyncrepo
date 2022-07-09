import pytest
import asyncio


def async_test(func):
    func = pytest.mark.asyncio(func)
    async def wrapper(*args, **kwargs):
        r = await func(*args, **kwargs)
        # https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
        await asyncio.sleep(0.25)
        return r
    return wrapper
