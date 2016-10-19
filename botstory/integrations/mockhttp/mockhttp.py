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
    def __init__(self, get={}, post=True, start=True, stop=True):
        self.get = aiohttp.test_utils.make_mocked_coro(return_value=get)
        self.post = aiohttp.test_utils.make_mocked_coro(return_value=post)
        self.start = aiohttp.test_utils.make_mocked_coro(return_value=start)
        self.stop = aiohttp.test_utils.make_mocked_coro(return_value=stop)
        self.webhook = stub('webhook')
