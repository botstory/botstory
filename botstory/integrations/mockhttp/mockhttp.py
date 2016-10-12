from unittest import mock
import aiohttp


def stub(name=None):
    """
    Creates a stub method. It accepts any arguments. Ideal to register to
    callbacks in tests.
    :param name: the constructed stub's name as used in repr
    :rtype: mock.MagicMock
    :return: Stub object.
    """
    return mock.MagicMock(spec=lambda *args, **kwargs: None, name=name)


class MockHttpInterface:
    post = aiohttp.test_utils.make_mocked_coro(return_value=True)
    listen_webhook = aiohttp.test_utils.make_mocked_coro(return_value=True)
    start = aiohttp.test_utils.make_mocked_coro(return_value=True)
    stop = aiohttp.test_utils.make_mocked_coro(return_value=True)

    # async def post(self, *args, **kwargs):
    #     stub('post')(*args, **kwargs)
    #
    # def listen_webhook(self, *args, **kwargs):
    #     stub('post')(*args, **kwargs)
    #
    # async def start(self, *args, **kwargs):
    #     stub('start')(*args, **kwargs)
    #
    # async def stop(self, *args, **kwargs):
    #     stub('stop')(*args, **kwargs)
