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
    webhook = stub('webhook')
    start = aiohttp.test_utils.make_mocked_coro(return_value=True)
    stop = aiohttp.test_utils.make_mocked_coro(return_value=True)
