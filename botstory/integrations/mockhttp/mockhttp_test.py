import importlib
from .. import mockhttp
from ... import di


def test_get_as_deps():
    # TODO: require reload aiohttp module because somewhere is used global di.clear()
    importlib.reload(mockhttp.mockhttp)
    importlib.reload(mockhttp)
    assert isinstance(di.injector.get('http'), mockhttp.MockHttpInterface)
