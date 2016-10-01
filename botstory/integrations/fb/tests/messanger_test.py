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
            interface.session = session
            chat.add_interface(interface)
            await chat.say('hi there!', user,
                           # TODO: temporal hack to mock session
                           session=session)

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
