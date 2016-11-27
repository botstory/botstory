import pytest
from .. import mockhttp
from ... import di, story


def test_get_mockhttp_as_dep():
    story.use(mockhttp.MockHttpInterface())

    with di.child_scope():
        @di.desc()
        class OneClass:
            @di.inject()
            def deps(self, http):
                self.http = http

        assert isinstance(di.injector.get('one_class').http, mockhttp.MockHttpInterface)
