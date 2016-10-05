import logging
import pytest

from . import db
from ..fb import messenger
from ... import story, utils

logger = logging.getLogger(__name__)


def teardown_function(function):
    logger.debug('tear down!')
    story.stories_library.clear()


@pytest.fixture
@pytest.mark.asyncio
def open_db(event_loop):
    class AsyncDBConnection:
        def __init__(self):
            self.db_interface = db.MongodbInterface(uri='mongo', db_name='test')

        async def __aenter__(self):
            await self.db_interface.connect(loop=event_loop)
            return self.db_interface

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            self.db_interface = None

    return AsyncDBConnection


@pytest.mark.asyncio
async def test_store_restore_user(open_db):
    async with open_db() as db_interface:
        user = utils.build_fake_user()

        user_id = await db_interface.set_user(user)
        restored_user = await db_interface.get_user(id=user_id)

        assert user.items() == restored_user.items()


@pytest.mark.asyncio
async def test_store_restore_session(open_db):
    async with open_db() as db_interface:
        session = utils.build_fake_session()
        session_id = await db_interface.set_session(session)
        logger.debug('session_id')
        logger.debug(session_id)
        restored_session = await db_interface.get_session(session_id=session_id)
        logger.debug('restored_session')
        logger.debug(restored_session)
        restored_session = await db_interface.get_session(user_id=session['user_id'])

        for (key, value) in restored_session.items():
            if key not in ['_id']:
                logger.debug('key {} '.format(key))
                assert session[key] == restored_session[key]


# TODO: build user and session from scratch
@pytest.mark.asyncio
async def test_integrate_with_facebook(open_db):
    async with open_db() as db_interface:
        user = utils.build_fake_user()
        session = utils.build_fake_session(user=user)

        await db_interface.set_session(session)
        await db_interface.set_user(user)

        interface = messenger.FBInterface(token='qwerty')
        interface.add_storage(db_interface)

        story.story_processor_instance.add_interface(interface)

        trigger = utils.SimpleTrigger()

        @story.on('hello, world!')
        def correct_story():
            @story.part()
            def store_result(message):
                trigger.receive(message)

        await interface.handle([
            {
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
            }
        ])

        del trigger.value['session']
        assert trigger.value == {
            'user': user,
            'data': {
                'text': {
                    'raw': 'hello, world!'
                }
            }
        }
