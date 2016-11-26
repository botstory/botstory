import pytest
from .. import mockhttp
from ... import di, story


@pytest.mark.skip()
def test_get_mockhttp_as_dep():
    story.use(mockhttp.MockHttpInterface())

    @di.desc()
    class OneClass:
        @di.inject()
        def deps(self, http):
            self.http = http

    assert isinstance(di.injector.get('one_class').http, mockhttp.MockHttpInterface)
