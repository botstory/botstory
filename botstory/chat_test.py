import aiohttp
import logging
import pytest

from botstory.middlewares import location
import botstory.integrations.fb.messenger
from . import Story
from .utils import answer, build_fake_session, build_fake_user, SimpleTrigger

logger = logging.getLogger(__name__)

story = None


def teardown_function(function):
    logger.debug('tear down!')
    story.clear()


@pytest.fixture()
def mock_interface(mocker):
    mocker.patch.object(
        botstory.integrations.fb.messenger.FBInterface,
        'send_text_message',
        aiohttp.test_utils.make_mocked_coro('something'),
    )
    mocker.patch.object(
        botstory.integrations.fb.messenger.FBInterface,
        'send_list',
        aiohttp.test_utils.make_mocked_coro('something'),
    )
    return botstory.integrations.fb.messenger.FBInterface()


@pytest.mark.asyncio
async def test_should_say(mock_interface):
    session = build_fake_session()
    user = build_fake_user()

    global story
    story = Story()
    story.use(mock_interface)

    @story.on('hi there!')
    def one_story():
        @story.part()
        async def then(message):
            await story.say('Nice to see you!', message['user'])

    await answer.pure_text('hi there!', session, user, story)

    mock_interface.send_text_message.assert_called_once_with(
        recipient=user,
        text='Nice to see you!',
        options=None,
    )


# TODO: move to middlewares/location/test_location.py
@pytest.mark.asyncio
@pytest.mark.skip
async def test_ask_location(mock_interface):
    session = build_fake_session()
    user = build_fake_user()

    global story
    story = Story()
    story.use(mock_interface)

    @story.on('SOS!')
    def one_story():
        @story.part()
        async def then(message):
            await story.ask_location('Hey, bro! Where is your rocket?', message['user'])

    await answer.pure_text('SOS!', session, user, story)

    mock_interface.send_text_message.assert_called_once_with(user, text='Hey, bro! Where is your rocket?')


@pytest.mark.asyncio
@pytest.mark.skip
async def test_get_location_as_result_of_asking_of_location(mock_interface):
    session = build_fake_session()
    user = build_fake_user()

    trigger = SimpleTrigger()

    global story
    story = Story()
    story.use(mock_interface)

    @story.on('SOS!')
    def one_story():
        @story.part()
        def then(ctx):
            return story.ask_location('Hey, bro! Where is your rocket?', ctx['user'])

        @story.part()
        def then(ctx):
            trigger.receive(location.get_location(ctx))

    await answer.pure_text('SOS!', session, user, story)
    await answer.location('somewhere', session, user, story)

    assert trigger.result() == 'somewhere'


@pytest.mark.asyncio
async def test_should_list_elements(mock_interface):
    with answer.Talk() as talk:
        story = talk.story
        story.use(mock_interface)

        @story.on('hi there!')
        def one_story():
            @story.part()
            async def then(ctx):
                await story.list_elements(elements=[{
                    'title': 'Classic T-Shirt Collection',  # (*) required
                    'image_url': 'https://peterssendreceiveapp.ngrok.io/img/collection.png',
                    'subtitle': 'See all our colors',
                    'default_action': {
                        'type': 'web_url',
                        'url': 'https://peterssendreceiveapp.ngrok.io/shop_collection',
                        'messenger_extensions': True,
                        'webview_height_ratio': 'tall',
                        'fallback_url': 'https://peterssendreceiveapp.ngrok.io/'
                    },
                    'buttons': [{
                        'title': 'View',
                        'type': 'web_url',
                        'url': 'https://peterssendreceiveapp.ngrok.io/collection',
                        'messenger_extensions': True,
                        'webview_height_ratio': 'tall',
                        'fallback_url': 'https://peterssendreceiveapp.ngrok.io/'
                    }]
                }, {
                    'title': 'Classic White T-Shirt',
                    'image_url': 'https://peterssendreceiveapp.ngrok.io/img/white-t-shirt.png',
                    'subtitle': '100% Cotton, 200% Comfortable',
                    'default_action': {
                        'type': 'web_url',
                        'url': 'https://peterssendreceiveapp.ngrok.io/view?item=100',
                        'messenger_extensions': True,
                        'webview_height_ratio': 'tall',
                        'fallback_url': 'https://peterssendreceiveapp.ngrok.io/'
                    },
                    'buttons': [{
                        'title': 'Shop Now',
                        'type': 'web_url',
                        'url': 'https://peterssendreceiveapp.ngrok.io/shop?item=100',
                        'messenger_extensions': True,
                        'webview_height_ratio': 'tall',
                        'fallback_url': 'https://peterssendreceiveapp.ngrok.io/'
                    }]
                }], buttons=[{
                    'title': 'View More',
                    'payload': 'payload',
                }], user=ctx['user'])

        await talk.ask('hi there!')

        mock_interface.send_list.assert_called_once_with(
            recipient=talk.user,
            elements=[{
                'title': 'Classic T-Shirt Collection',  # (*) required
                'image_url': 'https://peterssendreceiveapp.ngrok.io/img/collection.png',
                'subtitle': 'See all our colors',
                'default_action': {
                    'type': 'web_url',
                    'url': 'https://peterssendreceiveapp.ngrok.io/shop_collection',
                    'messenger_extensions': True,
                    'webview_height_ratio': 'tall',
                    'fallback_url': 'https://peterssendreceiveapp.ngrok.io/'
                },
                'buttons': [{
                    'title': 'View',
                    'type': 'web_url',
                    'url': 'https://peterssendreceiveapp.ngrok.io/collection',
                    'messenger_extensions': True,
                    'webview_height_ratio': 'tall',
                    'fallback_url': 'https://peterssendreceiveapp.ngrok.io/'
                }]
            }, {
                'title': 'Classic White T-Shirt',
                'image_url': 'https://peterssendreceiveapp.ngrok.io/img/white-t-shirt.png',
                'subtitle': '100% Cotton, 200% Comfortable',
                'default_action': {
                    'type': 'web_url',
                    'url': 'https://peterssendreceiveapp.ngrok.io/view?item=100',
                    'messenger_extensions': True,
                    'webview_height_ratio': 'tall',
                    'fallback_url': 'https://peterssendreceiveapp.ngrok.io/'
                },
                'buttons': [{
                    'title': 'Shop Now',
                    'type': 'web_url',
                    'url': 'https://peterssendreceiveapp.ngrok.io/shop?item=100',
                    'messenger_extensions': True,
                    'webview_height_ratio': 'tall',
                    'fallback_url': 'https://peterssendreceiveapp.ngrok.io/'
                }]
            }], buttons=[{
                'title': 'View More',
                'payload': 'payload',
            }],
        )
