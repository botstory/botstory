import asyncio
import pytest

from .. import fb, aiohttp
from ... import story, chat, utils


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

                # TODO: should be story.start()

                await http_integration.start()

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
