import pytest

from . import story
from . import chat
from .utils import answer, build_fake_user, SimpleTrigger


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

    answer.pure_text('hi there!', user)

    mock_send_text_message.assert_called_once_with(user.id, text='Nice to see you!')


def test_ask_location(mocker):
    mock_send_text_message = mocker.patch('botstory.chat.messenger.send_text_message')
    mock_send_text_message.return_value = 'ok'

    user = build_fake_user()

    @story.on('SOS!')
    def one_story():
        @story.then()
        def then(message):
            chat.ask_location('Hey, bro! Where is your rocket?', message['user'])

    answer.pure_text('SOS!', user)

    mock_send_text_message.assert_called_once_with(user.id, text='Hey, bro! Where is your rocket?')


def test_get_location_as_result_of_asking_of_location(mocker):
    mock_send_text_message = mocker.patch('botstory.chat.messenger.send_text_message')
    mock_send_text_message.return_value = 'ok'
    user = build_fake_user()

    trigger = SimpleTrigger()

    @story.on('SOS!')
    def one_story():
        @story.then()
        def then(message):
            return chat.ask_location('Hey, bro! Where is your rocket?', message['user'])

        @story.then()
        def then(message):
            trigger.receive(message['location'])

    answer.pure_text('SOS!', user)
    answer.location('somewhere', user)

    assert trigger.result() == 'somewhere'
