import logging
import pytest
from . import option
from ... import chat, story
from ...utils import answer, build_fake_session, build_fake_user, SimpleTrigger

logger = logging.getLogger(__name__)


def setup_function(function):
    logger.debug('setup')
    chat.interfaces = {}
    story.stories_library.clear()


def test_should_ask_with_options():
    logger.debug('chat.interfaces')
    logger.debug(chat.interfaces)
    session = build_fake_session()
    user = build_fake_user()

    trigger = SimpleTrigger()

    @story.on('How are you?')
    def one_story():
        @story.part()
        def ask(message):
            return chat.ask(
                'I feel fine. How about you?',
                options=[{
                    'title': 'Good!',
                    'payload': {'health': 1},
                }, {
                    'title': 'Ugly!',
                    'payload': {'health': -1},
                }, {
                    'title': 'As usual',
                    'payload': {'health': 0},
                }],
                user=message['user'],
            )

        @story.part()
        def get_health(message):
            trigger.receive(message['data']['option'])

    answer.pure_text('How are you?', session, user)
    answer.option({'health': 1}, session, user)
    assert trigger.result() == {'health': 1}


def test_validate_option():
    session = build_fake_session()
    user = build_fake_user()

    trigger = SimpleTrigger()

    @story.on(receive=option.Any())
    def one_story():
        @story.part()
        def store_option(message):
            trigger.passed()

    answer.option({'engine': 'start'}, session, user)
    assert trigger.is_triggered


def test_validate_only_option():
    session = build_fake_session()
    user = build_fake_user()

    trigger = SimpleTrigger()

    @story.on(receive=option.Any())
    def one_story():
        @story.part()
        def store_option(message):
            trigger.passed()

    answer.pure_text('Start engine!', session, user)
    assert not trigger.is_triggered
