import importlib
from .. import mockdb
from ... import di


def test_get_as_deps():
    # TODO: require reload aiohttp module because somewhere is used global di.clear()
    importlib.reload(mockdb.db)
    importlib.reload(mockdb)
    assert isinstance(di.injector.get('storage'), mockdb.MockDB)
