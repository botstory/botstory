import pytest
from .. import mockhttp
from ... import di, Story


def test_get_mockhttp_as_dep():
    story = Story()
    story.use(mockhttp.MockHttpInterface())

    with di.child_scope():
        @di.desc()
        class OneClass:
            @di.inject()
            def deps(self, http):
                self.http = http

        assert isinstance(di.injector.get('one_class').http, mockhttp.MockHttpInterface)
