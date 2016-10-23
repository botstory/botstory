from aiohttp import test_utils
import json
import pytest
from . import AioHttpInterface
from ..tests.fake_server import fake_fb
from ..commonhttp import errors


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
        'status': 200,
        'content_type': 'application/json',
        'text': json.dumps({'message': 'Ok!'}),
    })
    http = AioHttpInterface(port=9876)
    http.webhook(uri='/webhook', handler=handler, token='qwerty')
    try:
        await http.start()
        res = await http.post_raw('http://localhost:9876/webhook', json={'message': 'Is there anybody in there?'})
        handler.assert_called_once_with({'message': 'Is there anybody in there?'})
        assert res['status'] == 200
        assert res['text'] == json.dumps({'message': 'Ok!'})
    finally:
        await http.stop()


@pytest.mark.asyncio
async def test_pass_validation_for_correct_request():
    http = AioHttpInterface(port=9876)
    http.webhook(uri='/webhook', handler=None, token='token-value')
    try:
        await http.start()
        res = await http.get_raw('http://localhost:9876/webhook', params={
            'hub.challenge': 'some-challenge',
            'hub.mode': 'subscribe',
            'hub.verify_token': 'token-value',
        })
        assert res['text'] == 'some-challenge'
    finally:
        await http.stop()


@pytest.mark.asyncio
async def test_reject_validation_for_incorrect_request():
    http = AioHttpInterface(port=9876)
    http.webhook(uri='/webhook', handler=None, token='token-value')
    try:
        await http.start()
        await http.get('http://localhost:9876/webhook', params={
            'something': 'incorrect',
        })
    except errors.HttpRequestError as err:
        assert err.code == 422
        assert err.message == 'Error, wrong validation token'
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


@pytest.mark.skip(reason='too long')
@pytest.mark.asyncio
async def test_get_400_from_wrong_domain():
    http = AioHttpInterface()
    try:
        await http.get('http://wrong-url')
    except errors.HttpRequestError as err:
        assert err.code == 400


@pytest.mark.asyncio
async def test_get_400_from_wrong_path():
    http = AioHttpInterface()
    try:
        await http.get('http://localhost:9876/webhook')
    except errors.HttpRequestError as err:
        assert err.code == 400


@pytest.mark.asyncio
async def test_post_to_wrong_path_get_400(event_loop):
    async with fake_fb.Server(event_loop) as server:
        async with server.session() as session:
            http = AioHttpInterface()
            http.session = session

            try:
                await http.post(fake_fb.URI.format('/v2.6/me/messages/mistake'), json={'message': 'hello world!'})
            except errors.HttpRequestError as err:
                assert err.code == 404


@pytest.mark.skip(reason='too long')
@pytest.mark.asyncio
async def test_post_400_from_wrong_domain():
    http = AioHttpInterface()
    try:
        await http.post('http://wrong-url')
    except errors.HttpRequestError as err:
        assert err.code == 400


@pytest.mark.asyncio
async def test_post_400_from_wrong_path():
    http = AioHttpInterface()
    try:
        await http.post('http://localhost:9876/webhook')
    except errors.HttpRequestError as err:
        assert err.code == 400
