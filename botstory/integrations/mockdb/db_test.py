import pytest
from .. import mockdb
from ... import di, story


@pytest.mark.skip()
def test_get_mockdb_as_dep():
    story.use(mockdb.MockDB())

    @di.desc()
    class OneClass:
        @di.inject()
        def deps(self, storage):
            self.storage = storage

    assert isinstance(di.injector.get('one_class').storage, mockdb.MockDB)
