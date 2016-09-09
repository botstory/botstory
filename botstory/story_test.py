import pytest

from . import chat, story
from .utils import answer, build_fake_session, build_fake_user, SimpleTrigger
from .middlewares.text import text
from .middlewares.location import location


@pytest.fixture
def teardown_function(function):
    print('tear down!')
    story.clear()


def test_should_run_sequence_of_parts():
    trigger_1 = SimpleTrigger()
    trigger_2 = SimpleTrigger()
    user = build_fake_user()
    session = build_fake_session()

    @story.on('hi there!')
    def one_story():
        @story.then()
        def then(message):
            trigger_1.passed()

        @story.then()
        def then(message):
            trigger_2.passed()

    answer.pure_text('hi there!', session, user)

    assert trigger_1.is_triggered
    assert trigger_2.is_triggered


def test_should_wait_for_answer_on_ask():
    trigger = SimpleTrigger()
    session = build_fake_session()
    user = build_fake_user()

    @story.on('hi there!')
    def one_story():
        @story.then()
        def then(message):
            return chat.ask('How are you?', message['user'])

        @story.then()
        def then(message):
            trigger.passed()

    answer.pure_text('hi there!', session, user)

    assert not trigger.is_triggered

    answer.pure_text('Great!', session, user)

    assert trigger.is_triggered


def test_should_prevent_other_story_to_start_until_we_waiting_for_answer():
    trigger_1 = SimpleTrigger()
    trigger_2 = SimpleTrigger()
    session = build_fake_session()
    user = build_fake_user()

    @story.on('hi there!')
    def one_story():
        @story.then()
        def then(message):
            return chat.ask('How are you?', message['user'])

        @story.then()
        def then(message):
            trigger_2.passed()

    @story.on('Great!')
    def one_story():
        @story.then()
        def then(message):
            trigger_1.passed()

    answer.pure_text('hi there!', session, user)
    answer.pure_text('Great!', session, user)

    assert trigger_2.is_triggered
    assert not trigger_1.is_triggered


def test_should_start_next_story_after_current_finished():
    trigger = SimpleTrigger()
    session = build_fake_session()
    user = build_fake_user()

    @story.on('hi there!')
    def one_story():
        @story.then()
        def then(message):
            return chat.ask('How are you?', message['user'])

        @story.then()
        def then(message):
            pass

    @story.on('Great!')
    def one_story():
        @story.then()
        def then(message):
            trigger.passed()

    answer.pure_text('hi there!', session, user)
    answer.pure_text('Great!', session, user)
    answer.pure_text('Great!', session, user)

    assert trigger.is_triggered


def test_should_match_group_of_matchers_between_parts_of_story():
    trigger_1 = SimpleTrigger()
    trigger_2 = SimpleTrigger()
    session = build_fake_session()
    user = build_fake_user()

    @story.on('hi there!')
    def one_story():
        @story.then()
        def then(message):
            return [text.Any(), location.Any()]

        @story.then()
        def then(message):
            trigger_1.passed()
            return [text.Any(), location.Any()]

        @story.then()
        def then(message):
            trigger_2.passed()

    answer.pure_text('hi there!', session, user)
    answer.location({'lat': 1, 'lng': 1}, session, user)
    answer.pure_text('hi there!', session, user)

    assert trigger_1.is_triggered
    assert trigger_2.is_triggered


def test_should_match_group_of_matchers_on_story_start():
    trigger = SimpleTrigger()
    session = build_fake_session()
    user = build_fake_user()

    @story.on(receive=['hi there!', location.Any()])
    def one_story():
        @story.then()
        def then(message):
            trigger.passed()

    answer.pure_text('hi there!', session, user)
    answer.location({'lat': 1,'lng': 1}, session, user)

    assert trigger.triggered_times == 2
