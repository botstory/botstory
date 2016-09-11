from ... import chat, story
from ...utils import answer, build_fake_session, build_fake_user, SimpleTrigger
import pytest


def test_should_ask_with_options(mocker):
    mock_send_text_message = mocker.patch('botstory.chat.messenger.send_text_message')
    mock_send_text_message.return_value = 'ok'

    session = build_fake_session()
    user = build_fake_user()

    trigger = SimpleTrigger()

    @story.on('How are you?')
    def one_story():
        @story.then()
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

        @story.then()
        def get_health(message):
            trigger.receive(message['option'])

    answer.pure_text('How are you?', session, user)
    answer.option({'health': 1}, session, user)
    assert trigger.result() == {'health': 1}
