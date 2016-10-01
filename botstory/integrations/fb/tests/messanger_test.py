import pytest

from . import fake_fb
from .. import messenger
from .... import chat, utils


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
            interface = messenger.FBInterface(token='qwerty')
            chat.add_interface(interface)
            # mock http session
            chat.web_session = session
            await chat.say('hi there!', user)

            assert len(server.history) > 0
            assert server.history[-1]['request'].content_type == 'application/json'
            res = await server.history[-1]['request'].json()
            assert res == {
                'recipient': {
                    'id': user.facebook_user_id,
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
            interface = messenger.FBInterface(token='qwerty')
            chat.add_interface(interface)

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
                    'id': user.facebook_user_id,
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
