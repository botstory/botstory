import logging
import os
import pytest

from .. import fb, aiohttp, mongodb
from ... import story, chat, utils

logger = logging.getLogger(__name__)


def teardown_function(function):
    logger.debug('tear down!')
    story.stories_library.clear()


@pytest.fixture
def build_context():
    async def builder(db, no_session=False, no_user=False):
        user = None
        if not no_user:
            user = utils.build_fake_user()
            await db.set_user(user)

        if not no_session:
            session = utils.build_fake_session(user=user)
            await db.set_session(session)

        story.use(db)
        interface = story.use(fb.FBInterface(token='qwerty'))

        return interface, user

    return builder


@pytest.fixture
@pytest.mark.asyncio
def open_db(event_loop):
    class AsyncDBConnection:
        def __init__(self):
            self.db_interface = mongodb.MongodbInterface(uri=os.environ.get('TEST_MONGODB_URL', 'mongo'),
                                                         db_name='test')

        async def __aenter__(self):
            await self.db_interface.connect(loop=event_loop)
            await self.db_interface.clear_collections()
            return self.db_interface

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            await self.db_interface.clear_collections()
            self.db_interface = None

    return AsyncDBConnection


@pytest.mark.asyncio
async def test_facebook_interface_should_use_aiohttp_to_post_message(event_loop):
    async with fb.tests.fake_fb.Server(event_loop) as server:
        async with server.session() as server_session:
            # 1) setup app

            try:
                story.use(fb.FBInterface())
                http_integration = story.use(aiohttp.AioHttpInterface(
                    loop=event_loop,
                ))

                await story.start()

                # 2) and test it

                # TODO: could be better. Mock http interface
                http_integration.session = server_session
                user = utils.build_fake_user()

                # 3) test

                await chat.say('Pryvit!', user=user)

                assert len(server.history) > 0
                req = server.history[-1]['request']
                assert req.content_type == 'application/json'
                assert await req.json() == {
                    'recipient': {
                        'id': user['facebook_user_id'],
                    },
                    'message': {
                        'text': 'Pryvit!'
                    }
                }
            finally:
                await http_integration.stop()


@pytest.mark.asyncio
async def test_integrate_mongodb_with_facebook(open_db, build_context):
    async with open_db() as mongodb:
        facebook, user = await build_context(mongodb)

        trigger = utils.SimpleTrigger()

        @story.on('hello, world!')
        def correct_story():
            @story.part()
            def store_result(message):
                trigger.receive(message)

        await facebook.handle([{
            'id': 'PAGE_ID',
            'time': 1473204787206,
            'messaging': [
                {
                    'sender': {
                        'id': user['facebook_user_id'],
                    },
                    'recipient': {
                        'id': 'PAGE_ID'
                    },
                    'timestamp': 1458692752478,
                    'message': {
                        'mid': 'mid.1457764197618:41d102a3e1ae206a38',
                        'seq': 73,
                        'text': 'hello, world!'
                    }
                }
            ]
        }])

        del trigger.value['session']
        assert trigger.value == {
            'user': user,
            'data': {
                'text': {
                    'raw': 'hello, world!'
                }
            }
        }


@pytest.mark.asyncio
async def test_integrate_mongodb_with_facebook_with_none_session(open_db, build_context):
    async with open_db() as mongodb:
        facebook, _ = await build_context(mongodb, no_session=True, no_user=True)

        trigger = utils.SimpleTrigger()

        @story.on('hello, world!')
        def correct_story():
            @story.part()
            def store_result_for_new_user(message):
                trigger.receive(message)

        await facebook.handle([{
            'id': 'PAGE_ID',
            'time': 1473204787206,
            'messaging': [
                {
                    'sender': {
                        'id': 'some-facebook-id',
                    },
                    'recipient': {
                        'id': 'PAGE_ID'
                    },
                    'timestamp': 1458692752478,
                    'message': {
                        'mid': 'mid.1457764197618:41d102a3e1ae206a38',
                        'seq': 73,
                        'text': 'hello, world!'
                    }
                }
            ]
        }])

        assert trigger.value
        assert trigger.value['data']['text']['raw'] == 'hello, world!'
        assert trigger.value['user']['facebook_user_id'] == 'some-facebook-id'
