import pytest
import importlib

from . import tracker
from .. import mocktracker
from ... import di, story


# TODO: should make scoped di
def teardown_function(function):
    di.clear()


def reload_mocktracker():
    # TODO: require reload aiohttp module because somewhere is used global di.clear()
    importlib.reload(mocktracker.tracker)
    importlib.reload(mocktracker)


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


def test_get_mock_tracker_as_dep():
    reload_mocktracker()

    story.use(mocktracker.MockTracker())

    @di.desc()
    class OneClass:
        @di.inject()
        def deps(self, tracker):
            self.tracker = tracker

    assert isinstance(di.injector.get('one_class').tracker, mocktracker.MockTracker)
