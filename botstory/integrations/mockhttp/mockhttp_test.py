import importlib
from .. import mockhttp
from ... import di, story


def reload_module():
    # TODO: require reload aiohttp module because somewhere is used global di.clear()
    importlib.reload(mockhttp.mockhttp)
    importlib.reload(mockhttp)


def test_get_as_deps():
    reload_module()

    story.use(mockhttp.MockHttpInterface())

    @di.desc()
    class OneClass:
        @di.inject()
        def deps(self, http):
            self.http = http

    assert isinstance(di.injector.get('one_class').http, mockhttp.MockHttpInterface)
