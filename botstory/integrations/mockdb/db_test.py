import importlib
from .. import mockdb
from ... import di, story


def teardown_function(function):
    di.clear()


def reload_module():
    # TODO: require reload aiohttp module because somewhere is used global di.clear()
    importlib.reload(mockdb.db)
    importlib.reload(mockdb)


def test_get_mockdb_as_dep():
    reload_module()

    story.use(mockdb.MockDB())

    @di.desc()
    class OneClass:
        @di.inject()
        def deps(self, storage):
            self.storage = storage

    assert isinstance(di.injector.get('one_class').storage, mockdb.MockDB)
