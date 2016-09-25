import logging
import pytest

from .. import chat, story
from ..utils import answer, build_fake_session, build_fake_user, SimpleTrigger

logger = logging.getLogger(__name__)


@pytest.fixture
def teardown_function(function):
    logger.debug('tear down!')
    story.stories_library.clear()


def test_begin_of_callable_story():
    trigger = SimpleTrigger()
    session = build_fake_session()

    @story.callable()
    def one_story():
        @story.part()
        def store_arguments(arg1, arg2):
            trigger.receive({
                'value1': arg1,
                'value2': arg2,
            })

    one_story(1, 2, session=session)

    assert trigger.result() == {
        'value1': 1,
        'value2': 2,
    }


def test_parts_of_callable_story():
    trigger_1 = SimpleTrigger()
    trigger_2 = SimpleTrigger()
    session = build_fake_session()
    user = build_fake_user()

    @story.callable()
    def meet_ava_story():
        @story.part()
        def ask_name(user):
            return chat.ask(
                'My name is Ava. What is your name?',
                user=user,
            )

        @story.part()
        def ask_age(message):
            trigger_1.passed()
            return chat.ask(
                'Nice to see you {}. What do you do here?'.format(message['text']['raw']),
                user=message['user'],
            )

        @story.part()
        def store_arguments(message):
            age = int(message['text']['raw'])
            if age < 30:
                res = 'You are so young! '
            else:
                res = 'Hm. Too old to die young'

            chat.say(res, user=message['user'])
            trigger_2.passed()

    meet_ava_story(user, session=session)

    answer.pure_text('Eugene', session, user=user)
    answer.pure_text('13', session, user=user)

    assert trigger_1.is_triggered
    assert trigger_2.is_triggered


def test_call_story_from_common_story():
    trigger = SimpleTrigger()

    session = build_fake_session()
    user = build_fake_user()

    @story.callable()
    def common_greeting():
        @story.part()
        def ask_name(user):
            return chat.ask(
                'Hi {}. How are you?'.format(user.name),
                user=user,
            )

    @story.on('Hi!')
    def meet():
        @story.part()
        def greeting(message):
            return common_greeting(
                user=message['user'],
                session=message['session'],
            )

        @story.part()
        def ask_location(message):
            return chat.ask(
                'Which planet are we going to visit today?',
                user=message['user'],
            )

        @story.part()
        def parse(message):
            trigger.receive(message['text']['raw'])

    answer.pure_text('Hi!', session, user=user)
    answer.pure_text('I\'m fine', session, user=user)
    answer.pure_text('Venus, as usual!', session, user=user)

    assert trigger.value == 'Venus, as usual!'


def test_parts_of_callable_story_can_be_sync():
    trigger_1 = SimpleTrigger()
    trigger_2 = SimpleTrigger()
    session = build_fake_session()

    @story.callable()
    def one_story():
        @story.part()
        def has():
            trigger_1.passed()

        @story.part()
        def so():
            trigger_2.passed()

    one_story(session=session)

    assert trigger_1.is_triggered
    assert trigger_2.is_triggered


def test_call_story_from_another_callable():
    trigger_1 = SimpleTrigger()
    trigger_2 = SimpleTrigger()
    session = build_fake_session()

    @story.callable()
    def one_story():
        @story.part()
        def so_1(session_1):
            pass

        @story.part()
        def so_2(session_2):
            another_story(session=session_2)

        @story.part()
        def so_3(session_3):
            trigger_2.passed()

    @story.callable()
    def another_story():
        @story.part()
        def has():
            pass

        @story.part()
        def so():
            trigger_1.passed()

    # push extra parameter with session
    # and it will propagate up to other story as well
    one_story(session, session=session)

    assert trigger_1.is_triggered
    assert trigger_2.is_triggered
