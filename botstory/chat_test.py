import aiohttp
import logging
import pytest

import botstory.integrations.fb.messenger
from . import story
from . import chat
from .utils import answer, build_fake_session, build_fake_user, SimpleTrigger

logger = logging.getLogger(__name__)


def setup_function(function):
    logger.debug('setup')
    chat.interfaces = {}
    story.stories_library.clear()


def teardown_function(function):
    logger.debug('tear down!')
    chat.interfaces = {}
    story.stories_library.clear()


@pytest.fixture()
def mock_interface(mocker):
    mocker.patch.object(
        botstory.integrations.fb.messenger.FBInterface,
        'send_text_message',
        aiohttp.test_utils.make_mocked_coro('something'),
    )
    return chat.add_interface(botstory.integrations.fb.messenger.FBInterface())


@pytest.mark.asyncio
async def test_should_say(mock_interface):
    session = build_fake_session()
    user = build_fake_user()

    @story.on('hi there!')
    def one_story():
        @story.part()
        async def then(message):
            await chat.say('Nice to see you!', message['user'])

    await answer.pure_text('hi there!', session, user)

    mock_interface.send_text_message.assert_called_once_with(
        recipient=user,
        text='Nice to see you!',
    )


# TODO: move to middlewares/location/test_location.py
@pytest.mark.asyncio
@pytest.mark.skip
async def test_ask_location(mock_interface):
    session = build_fake_session()
    user = build_fake_user()

    @story.on('SOS!')
    def one_story():
        @story.part()
        async def then(message):
            await chat.ask_location('Hey, bro! Where is your rocket?', message['user'])

    await answer.pure_text('SOS!', session, user)

    mock_interface.send_text_message.assert_called_once_with(user, text='Hey, bro! Where is your rocket?')


@pytest.mark.asyncio
@pytest.mark.skip
async def test_get_location_as_result_of_asking_of_location(mock_interface):
    session = build_fake_session()
    user = build_fake_user()

    trigger = SimpleTrigger()

    @story.on('SOS!')
    def one_story():
        @story.part()
        def then(message):
            return chat.ask_location('Hey, bro! Where is your rocket?', message['user'])

        @story.part()
        def then(message):
            trigger.receive(message['data']['location'])

    await answer.pure_text('SOS!', session, user)
    await answer.location('somewhere', session, user)

    assert trigger.result() == 'somewhere'
