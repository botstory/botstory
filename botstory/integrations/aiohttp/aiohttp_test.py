from aiohttp import test_utils
import pytest
from . import AioHttpInterface
from ..tests.fake_server import fake_fb


@pytest.mark.asyncio
async def test_post(event_loop):
    async with fake_fb.Server(event_loop) as server:
        async with server.session() as session:
            http = AioHttpInterface()
            http.session = session

            assert await http.post(fake_fb.URI.format('/v2.6/me/messages/'), json={'message': 'hello world!'})
            assert len(server.history) == 1
            req = server.history[-1]['request']
            assert req.content_type == 'application/json'
            assert await req.json() == {'message': 'hello world!'}


@pytest.mark.asyncio
async def test_listen_webhook():
    handler = test_utils.make_mocked_coro(return_value={
        'result': 'ok',
    })
    http = AioHttpInterface(port=9876)
    http.webhook(uri='/webhook', handler=handler)
    try:
        await http.start()
        res = await http.post('http://localhost:9876/webhook', json={'message': 'Is there anybody in there?'})
        handler.assert_called_once_with({'message': 'Is there anybody in there?'})
        assert res == {'result': 'ok'}
    finally:
        await http.stop()


@pytest.mark.asyncio
async def test_should_not_create_server_if_there_wasnt_any_webhooks():
    http = AioHttpInterface(port=9876)
    try:
        await http.start()
        assert not http.server
    finally:
        await http.stop()
