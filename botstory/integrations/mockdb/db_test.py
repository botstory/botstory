import pytest
from .. import mockdb
from ... import di, Story


def test_get_mockdb_as_dep():
    story = Story()

    story.use(mockdb.MockDB())

    with di.child_scope():
        @di.desc()
        class OneClass:
            @di.inject()
            def deps(self, storage):
                self.storage = storage

        assert isinstance(di.injector.get('one_class').storage, mockdb.MockDB)
