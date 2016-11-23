import pytest

from . import tracker
from .. import mocktracker
from ... import di, story


def test_event():
    t = tracker.MockTracker()
    t.event()


def test_new_message():
    t = tracker.MockTracker()
    t.new_message()


def test_new_user():
    t = tracker.MockTracker()
    t.new_user()


def test_story():
    t = tracker.MockTracker()
    t.story()


@pytest.mark.skip('DI does not work this way')
def test_get_mock_tracker_as_dep():
    # TODO: require reload aiohttp module because somewhere is used global di.clear()
    # importlib.reload(mocktracker.tracker)
    # importlib.reload(mocktracker)

    story.use(mocktracker.MockTracker())

    @di.inject()
    class OneClass:
        @di.inject()
        def deps(self, tracker):
            self.tracker = tracker

    assert isinstance(di.injector.get('one-class').tracker, mocktracker.MockTracker)
