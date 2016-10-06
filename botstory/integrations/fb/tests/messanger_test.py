import logging
import pytest

from . import fake_fb
from .. import messenger
from ... import mockdb
from .... import chat, story, utils
from ....middlewares.option import option

logger = logging.getLogger(__name__)


def teardown_function(function):
    logger.debug('tear down!')
    story.stories_library.clear()


@pytest.mark.asyncio
async def test_send_text_message(event_loop):
    user = utils.build_fake_user()
    async with fake_fb.Server(event_loop) as server:
        async with server.session() as session:
            interface = messenger.FBInterface(token='qwerty')
            interface.session = session
            res = await interface.send_text_message(
                session=session,
                recipient=user, text='hi!', options=None)
            assert res == {
                'status': 'ok',
            }


@pytest.mark.asyncio
async def test_integration(event_loop):
    user = utils.build_fake_user()
    async with fake_fb.Server(event_loop) as server:
        async with server.session() as session:
            story.use(messenger.FBInterface(token='qwerty'))
            story.use(mockdb.MockDB())

            # mock http session
            chat.web_session = session
            await chat.say('hi there!', user)

            assert len(server.history) > 0
            assert server.history[-1]['request'].content_type == 'application/json'
            res = await server.history[-1]['request'].json()
            assert res == {
                'recipient': {
                    'id': user['facebook_user_id'],
                },
                'message': {
                    'text': 'hi there!'
                }
            }


@pytest.mark.asyncio
async def test_options(event_loop):
    user = utils.build_fake_user()
    async with fake_fb.Server(event_loop) as server:
        async with server.session() as session:
            story.use(messenger.FBInterface(token='qwerty'))
            story.use(mockdb.MockDB())

            # mock web session
            chat.web_session = session

            await chat.ask(
                'Which color do you like?',
                options=[{
                    'title': 'Red',
                    'payload': 0xff0000,
                }, {
                    'title': 'Green',
                    'payload': 0x00ff00,
                }, {
                    'title': 'Blue',
                    'payload': 0x0000ff,
                }],
                user=user)

            assert len(server.history) > 0
            assert server.history[-1]['request'].content_type == 'application/json'
            res = await server.history[-1]['request'].json()
            assert res == {
                'recipient': {
                    'id': user['facebook_user_id'],
                },
                'message': {
                    'text': 'Which color do you like?',
                    'quick_replies': [
                        {
                            'content_type': 'text',
                            'title': 'Red',
                            'payload': 0xff0000,
                        },
                        {
                            'content_type': 'text',
                            'title': 'Green',
                            'payload': 0x00ff00,
                        },
                        {
                            'content_type': 'text',
                            'title': 'Blue',
                            'payload': 0x0000ff,
                        },
                    ],
                },
            }


@pytest.fixture
def build_fb_interface():
    async def builder():
        user = utils.build_fake_user()
        session = utils.build_fake_session()

        storage = story.use(mockdb.MockDB())
        fb = story.use(messenger.FBInterface(token='qwerty'))

        await storage.set_session(session)
        await storage.set_user(user)

        return fb

    return builder


@pytest.mark.asyncio
async def test_handler_raw_text(build_fb_interface):
    fb_interface = await build_fb_interface()

    correct_trigger = utils.SimpleTrigger()
    incorrect_trigger = utils.SimpleTrigger()

    @story.on('hello, world!')
    def correct_story():
        @story.part()
        def store_result(message):
            correct_trigger.receive(message)

    @story.on('Goodbye, world!')
    def incorrect_story():
        @story.part()
        def store_result(message):
            incorrect_trigger.receive(message)

    await fb_interface.handle([
        {
            "id": "PAGE_ID",
            "time": 1473204787206,
            "messaging": [
                {
                    "sender": {
                        "id": "USER_ID"
                    },
                    "recipient": {
                        "id": "PAGE_ID"
                    },
                    "timestamp": 1458692752478,
                    "message": {
                        "mid": "mid.1457764197618:41d102a3e1ae206a38",
                        "seq": 73,
                        "text": "hello, world!"
                    }
                }
            ]
        }
    ])

    assert incorrect_trigger.value is None
    assert correct_trigger.value == {
        'user': fb_interface.storage.user,
        'session': fb_interface.storage.session,
        'data': {
            'text': {
                'raw': 'hello, world!'
            }
        }
    }


@pytest.mark.asyncio
async def test_handler_selected_option(build_fb_interface):
    fb_interface = await build_fb_interface()

    correct_trigger = utils.SimpleTrigger()
    incorrect_trigger = utils.SimpleTrigger()

    @story.on(receive=option.Match('GREEN'))
    def correct_story():
        @story.part()
        def store_result(message):
            correct_trigger.receive(message)

    @story.on(receive=option.Match('BLUE'))
    def incorrect_story():
        @story.part()
        def store_result(message):
            incorrect_trigger.receive(message)

    await fb_interface.handle([
        {
            "id": "PAGE_ID",
            "time": 1473204787206,
            "messaging": [
                {
                    "sender": {
                        "id": "USER_ID"
                    },
                    "recipient": {
                        "id": "PAGE_ID"
                    },
                    "timestamp": 1458692752478,
                    "message": {
                        "mid": "mid.1457764197618:41d102a3e1ae206a38",
                        "seq": 73,
                        "text": "Green!",
                        "quick_reply": {
                            "payload": "GREEN"
                        }
                    }
                }
            ]
        }
    ])

    assert incorrect_trigger.value is None
    assert correct_trigger.value == {
        'user': fb_interface.storage.user,
        'session': fb_interface.storage.session,
        'data': {
            'option': 'GREEN',
            'text': {
                'raw': 'Green!'
            }
        }
    }
