import aiohttp
from aiohttp.helpers import sentinel
import json
from unittest import mock


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
    def __init__(self, get={}, get_raise=sentinel,
                 post=True, post_raise=sentinel,
                 start=True,
                 stop=True):
        self.get = aiohttp.test_utils.make_mocked_coro(
            return_value=get,
            raise_exception=get_raise,
        )
        self.get_raw = aiohttp.test_utils.make_mocked_coro(
            return_value={'text': json.dumps(get), 'status': 200, },
            raise_exception=get_raise,
        )
        self.post = aiohttp.test_utils.make_mocked_coro(
            return_value=post,
            raise_exception=post_raise,
        )
        self.post_raw = aiohttp.test_utils.make_mocked_coro(
            return_value={'text': json.dumps(post), 'status': 200, },
            raise_exception=post_raise,
        )
        self.start = aiohttp.test_utils.make_mocked_coro(return_value=start)
        self.stop = aiohttp.test_utils.make_mocked_coro(return_value=stop)
        self.webhook = stub('webhook')
