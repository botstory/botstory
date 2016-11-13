import asyncio


def add(fn):
    asyncio.get_event_loop().call_soon_threadsafe(fn)
