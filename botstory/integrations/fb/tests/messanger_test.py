import pytest

from . import fake_fb
from .. import messenger


@pytest.mark.asyncio
async def test_send_text_message(event_loop):
    async with fake_fb.Server(event_loop) as server:
        async with server.session() as session:
            interface = messenger.FBInterface(token='qwerty')
            interface.session = session
            res = await interface.async_send_text_message(recipient_id='123123',
                                                          text='hi!', options=None)
            assert res == {
                'status': 'ok',
            }
