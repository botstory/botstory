from . import tracker


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
