import pytest

from . import story
from . import chat
from .utils import build_fake_user, SimpleTrigger, matchers


@pytest.fixture
def teardown_function(function):
    print('tear down!')
    story.clear()


def test_should_say(mocker):
    mock_send_text_message = mocker.patch('botstory.chat.messenger.send_text_message')
    mock_send_text_message.return_value = 'ok'

    user = build_fake_user()

    @story.on('hi there!')
    def one_story():
        @story.then()
        def then(message):
            chat.say('Nice to see you!', message['user'])

    matchers.pure_text('hi there!', user)

    mock_send_text_message.assert_called_once_with(user.id, text='Nice to see you!')
