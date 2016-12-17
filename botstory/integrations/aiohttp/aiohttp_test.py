from aiohttp import test_utils
import json
import pytest
from . import AioHttpInterface
from .. import aiohttp
from ..commonhttp import errors
from ..tests import fake_server
from ... import di, Story

story = None


def teardown_function(function):
    story and story.clear()


@pytest.fixture
def webhook_handler():
    return test_utils.make_mocked_coro(return_value={
        'status': 200,
        'content_type': 'application/json',
        'text': json.dumps({'message': 'Ok!'}),
    })


@pytest.mark.asyncio
async def test_post(event_loop):
    async with fake_server.FakeFacebook(event_loop) as server:
        async with server.session() as session:
            http = AioHttpInterface()
            http.session = session

            assert await http.post(fake_server.URI.format('/v2.6/me/messages/'), json={'message': 'hello world!'})
            assert len(server.history) == 1
            req = server.history[-1]['request']
            assert req.content_type == 'application/json'
            assert await req.json() == {'message': 'hello world!'}


@pytest.mark.asyncio
async def test_listen_webhook(webhook_handler):
    http = AioHttpInterface(port=9876)
    http.webhook(uri='/webhook', handler=webhook_handler, token='qwerty')
    try:
        await http.start()
        res = await http.post_raw('http://localhost:9876/webhook', json={'message': 'Is there anybody in there?'})
        webhook_handler.assert_called_once_with({'message': 'Is there anybody in there?'})
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
@pytest.mark.asynciod
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
    async with fake_server.FakeFacebook(event_loop) as server:
        async with server.session() as session:
            http = AioHttpInterface()
            http.session = session

            try:
                await http.post(fake_server.URI.format('/v2.6/me/messages/mistake'), json={'message': 'hello world!'})
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


@pytest.mark.asyncio
async def test_delete_200(event_loop):
    async with fake_server.FakeFacebook(event_loop) as server:
        async with server.session() as session:
            http = AioHttpInterface()
            http.session = session

            await http.delete(fake_server.URI.format('/v2.6/me/thread_settings'))


@pytest.mark.asyncio
async def test_delete_400(event_loop):
    async with fake_server.FakeFacebook(event_loop) as server:
        async with server.session() as session:
            http = AioHttpInterface()
            http.session = session

            try:
                await http.delete(fake_server.URI.format('/v2.6/me/wrong'))
            except errors.HttpRequestError as err:
                assert err.code == 404


@pytest.mark.asyncio
async def test_pass_middleware(mocker, webhook_handler):
    handler_stub = mocker.stub()

    def MockMiddleware():
        async def middleware_factory(app, handler):
            async def mock_middleware_handler(request):
                handler_stub(request)
                return await handler(request)

            return mock_middleware_handler

        return middleware_factory

    try:
        http = AioHttpInterface(middlewares=[MockMiddleware()], port=8080)
        http.webhook(uri='/webhook', handler=webhook_handler, token='qwerty')
        await http.start()
        await http.post('http://localhost:8080/webhook', json={})
        assert handler_stub.called
    finally:
        await http.stop()


def test_get_as_deps():
    global story
    story = Story()
    story.use(aiohttp.AioHttpInterface())

    with di.child_scope('http'):
        @di.desc()
        class OneClass:
            @di.inject()
            def deps(self, http):
                self.http = http

        assert isinstance(di.injector.get('one_class').http, aiohttp.AioHttpInterface)


@pytest.mark.asyncio
async def test_shop_should_remove_app():
    http = aiohttp.AioHttpInterface()
    assert not http.has_app()
    http.get_app()
    assert http.has_app()
    await http.stop()
    assert not http.has_app()


@pytest.mark.asyncio
async def test_should_raise_exception_on_webhook_if_aiohttp_already_is_started(webhook_handler):
    http = aiohttp.AioHttpInterface()
    http.get_app()
    await http.start()
    with pytest.raises(aiohttp.WebhookException):
        http.webhook(uri='/webhook', handler=webhook_handler, token='qwerty')
