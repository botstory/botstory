import aiohttp
from aiohttp import errors, web
import asyncio
import logging
import json as _json
import urllib
from yarl import URL

from ..commonhttp import errors as common_errors, statuses
from ... import di

logger = logging.getLogger(__name__)


class WebhookHandler:
    def __init__(self, handler):
        self.handler = handler

    async def handle(self, request):
        res = await self.handler(await request.json())
        return web.Response(**res)


def is_ok(status):
    return 200 <= status < 400


class WebhookException(Exception):
    pass


@di.desc('http', reg=False)
class AioHttpInterface:
    def __init__(self, host='0.0.0.0', port=None,
                 shutdown_timeout=60.0, ssl_context=None,
                 backlog=128, auto_start=True,
                 middlewares=[],
                 ):
        if port is None:
            if not ssl_context:
                port = 8080
            else:
                port = 8443

        self.backlog = backlog
        self.host = host
        self.middlewares = middlewares
        self.port = port
        self.shutdown_timeout = shutdown_timeout

        self.ssl_context = ssl_context
        self.auto_start = auto_start

        self.app = None
        self.session = None
        self.server = None
        self.handler = None
        self.webhook_token = None

    async def get(self, url, params=None, headers=None):
        logger.debug('get url={}'.format(url))
        loop = asyncio.get_event_loop()
        with aiohttp.ClientSession(loop=loop) as session:
            return await(await self.method(
                method_type='get',
                session=session,
                url=url,
                params=params,
                headers=headers,
            )).json()

    async def get_raw(self, url, params=None, headers=None):
        logger.debug('get url={}'.format(url))
        loop = asyncio.get_event_loop()
        with aiohttp.ClientSession(loop=loop) as session:
            res = await self.method(
                method_type='get',
                session=session,
                url=url,
                params=params,
                headers=headers,
            )
            return {
                'status': res.status,
                'headers': res.headers,
                'text': await res.text(),
            }

    async def post(self, url, params=None, headers=None, json=None):
        logger.debug('post url={}'.format(url))
        headers = headers or {}
        headers['Content-Type'] = headers.get('Content-Type', 'application/json')
        loop = asyncio.get_event_loop()
        with aiohttp.ClientSession(loop=loop) as session:
            return await(await self.method(
                method_type='post',
                session=session,
                url=url,
                params=params,
                headers=headers,
                data=_json.dumps(json),
            )).json()

    async def post_raw(self, url, params=None, headers=None, json=None):
        logger.debug('post url={}'.format(url))
        headers = headers or {}
        headers['Content-Type'] = headers.get('Content-Type', 'application/json')
        loop = asyncio.get_event_loop()
        with aiohttp.ClientSession(loop=loop) as session:
            res = await self.method(
                method_type='post',
                session=session,
                url=url,
                params=params,
                headers=headers,
                data=_json.dumps(json),
            )
            return {
                'status': res.status,
                'headers': res.headers,
                'text': await res.text(),
            }

    async def delete(self, url, params=None, headers=None, json=None):
        logger.debug('delete url={}'.format(url))
        headers = headers or {}
        headers['Content-Type'] = headers.get('Content-Type', 'application/json')
        loop = asyncio.get_event_loop()
        with aiohttp.ClientSession(loop=loop) as session:
            return await(await self.method(
                method_type='delete',
                session=session,
                url=url,
                params=params,
                headers=headers,
                data=_json.dumps(json),
            )).json()

    async def method(self, method_type, session, url, **kwargs):
        # be able to mock session from outside
        session = self.session or session
        try:
            try:
                method_name = getattr(session, method_type)
                resp = await method_name(
                    url,
                    **kwargs,
                )
            except errors.ClientOSError as err:
                raise common_errors.HttpRequestError(
                    code=400,
                    message='{} {}'.format(err.errno, err.strerror),
                )
            if not is_ok(resp.status):
                raise common_errors.HttpRequestError(
                    code=resp.status,
                    headers=resp.headers,
                    message=await resp.text(),
                )
        except Exception as err:
            logger.warn(
                'Exception: status: {status}, message: {message}, type: {type}, method: {method}, url: {url}, {kwargs}'
                    .format(status=getattr(err, 'code', None),
                            message=getattr(err, 'message', None),
                            type=type(err),
                            method=method_name,
                            url=url,
                            kwargs=kwargs,
                            )
            )
            raise err
        return resp

    def get_app(self):
        if not self.has_app():
            loop = asyncio.get_event_loop()
            logger.debug('create web app')
            self.app = web.Application(
                loop=loop,
                middlewares=self.middlewares,
            )
        return self.app

    def has_app(self):
        return self.app is not None

    def webhook(self, uri, handler, token):
        logger.debug('register webhook {}'.format(uri))
        self.webhook_token = token
        if self.get_app().frozen:
            raise WebhookException('Aiohttp extension is already started. '
                                   'We should change webhook before aiohttp is started.')
        self.get_app().router.add_get(uri, self.handle_webhook_validation)
        self.get_app().router.add_post(uri, WebhookHandler(handler).handle)

    def handle_webhook_validation(self, request):
        params = {name: value[0] for name, value in urllib.parse.parse_qs(request.query_string).items()}
        logger.debug('try to validate webhook with {}'.format(params))
        if params.get('hub.verify_token', None) == self.webhook_token and \
                        params.get('hub.mode', None) == 'subscribe':
            return web.Response(text=params.get('hub.challenge'))
        else:
            return web.Response(text='Error, wrong validation token',
                                status=statuses.HTTP_422_UNPROCESSABLE_ENTITY)

    async def start(self):
        logger.debug('start')
        if not self.has_app():
            logger.debug('does not have app')
            return
        if not self.auto_start:
            logger.debug('should not start automatically')
            return
        app = self.get_app()
        handler = app.make_handler()
        loop = asyncio.get_event_loop()
        server = loop.create_server(
            handler,
            self.host,
            self.port,
            ssl=self.ssl_context,
            backlog=self.backlog,
        )

        srv, startup_res = await asyncio.gather(
            server, app.startup(),
            loop=loop,
        )

        scheme = 'https' if self.ssl_context else 'http'
        url = URL('{}://localhost'.format(scheme))
        url = url.with_host(self.host).with_port(self.port)
        logger.debug('======== Running on {} ========\n'
                     '(Press CTRL+C to quit)'.format(url))

        self.server = srv
        self.handler = handler

    async def stop(self):
        logger.debug('stop')

        if not self.has_app():
            logger.debug('does not have app')
            return

        if self.server:
            self.server.close()
            await self.server.wait_closed()

        await self.app.shutdown()
        await self.app.cleanup()
        self.app = None

        if self.handler:
            await self.handler.finish_connections(self.shutdown_timeout)
