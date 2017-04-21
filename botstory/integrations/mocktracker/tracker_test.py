import pytest

from . import tracker
from .. import mocktracker
from ... import di, Story

story = None


def teardown_function(function):
    story and story.clear()


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
    global story
    story = Story()
    story.use(mocktracker.MockTracker())

    with di.child_scope():
        @di.desc()
        class OneClass:
            @di.inject()
            def deps(self, tracker):
                self.tracker = tracker

        assert isinstance(di.injector.get('one_class').tracker, mocktracker.MockTracker)
