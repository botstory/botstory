import asyncio
import pytest

from .locations import Location
from ... import story
from ...story import clear, match_message
from ...utils import build_fake_user, matchers, SimpleTrigger


def teardown_function(function):
    print('tear down!')
    clear()


def test_should_trigger_on_any_location():
    trigger = SimpleTrigger()
    user = build_fake_user()

    @story.on(receive=Location.Any())
    def one_story():
        @story.then()
        def then(message):
            trigger.passed()

    match_message({
        'location': {
            'lat': 1,
            'lng': 1,
        },
        'user': user,
    })
    assert trigger.is_triggered


def test_should_not_react_on_common_message():
    trigger = SimpleTrigger()
    user = build_fake_user()

    @story.on(receive=Location.Any())
    def one_story():
        @story.then()
        def then(message):
            trigger.passed()

    matchers.pure_text('Hey!', user)

    assert not trigger.is_triggered
