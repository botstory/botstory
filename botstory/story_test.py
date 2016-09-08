import pytest

from . import story
from . import chat
from .utils import build_fake_user, SimpleTrigger, matchers


@pytest.fixture
def teardown_function(function):
    print('tear down!')
    story.clear()


def test_should_run_sequence_of_parts():
    trigger_1 = SimpleTrigger()
    trigger_2 = SimpleTrigger()
    user = build_fake_user()

    @story.on('hi there!')
    def one_story():
        @story.then()
        def then(message):
            trigger_1.passed()

        @story.then()
        def then(message):
            trigger_2.passed()

    matchers.pure_text('hi there!', user)

    assert trigger_1.is_triggered
    assert trigger_2.is_triggered


def test_should_wait_for_answer_on_ask():
    trigger = SimpleTrigger()
    user = build_fake_user()

    @story.on('hi there!')
    def one_story():
        @story.then()
        def then(message):
            return chat.ask('How are you?', message.user)

        @story.then()
        def then(message):
            trigger.passed()

    matchers.pure_text('hi there!', user)

    assert not trigger.is_triggered

    matchers.pure_text('Great!', user)

    assert trigger.is_triggered


def test_should_prevent_other_story_to_start_until_we_waiting_for_answer():
    trigger = SimpleTrigger()
    user = build_fake_user()

    @story.on('hi there!')
    def one_story():
        @story.then()
        def then(message):
            return chat.ask('How are you?', message.user)

        @story.then()
        def then(message):
            pass

    @story.on('Great!')
    def one_story():
        @story.then()
        def then(message):
            trigger.passed()

    matchers.pure_text('hi there!', user)
    matchers.pure_text('Great!', user)

    assert not trigger.is_triggered


def test_should_start_next_story_after_current_finished():
    trigger = SimpleTrigger()
    user = build_fake_user()

    @story.on('hi there!')
    def one_story():
        @story.then()
        def then(message):
            return chat.ask('How are you?', message.user)

        @story.then()
        def then(message):
            pass

    @story.on('Great!')
    def one_story():
        @story.then()
        def then(message):
            trigger.passed()

    matchers.pure_text('hi there!', user)
    matchers.pure_text('Great!', user)
    matchers.pure_text('Great!', user)

    assert trigger.is_triggered
