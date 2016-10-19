import aiohttp
from aiohttp import web
import asyncio
import logging
import json as _json
import urllib
from yarl import URL

logger = logging.getLogger(__name__)

HTTP_422_UNPROCESSABLE_ENTITY = 422


class WebhookHandler:
    def __init__(self, handler):
        self.handler = handler

    async def handle(self, request):
        res = await self.handler(await request.json())
        return web.Response(text=_json.dumps(res))


class AioHttpInterface:
    type = 'interface.aiohttp'

    def __init__(self, host='0.0.0.0', port=None,
                 shutdown_timeout=60.0, ssl_context=None,
                 backlog=128, auto_start=True,
                 ):
        if port is None:
            if not ssl_context:
                port = 8080
            else:
                port = 8443

        self.backlog = backlog
        self.host = host
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
            # be able to mock session from outside
            session = self.session or session
            resp = await session.get(
                url,
                params=params,
                headers=headers,
            )
            return await resp.text()

    async def post(self, url, params=None, headers=None, json=None):
        logger.debug('post url={}'.format(url))
        headers = headers or {}
        headers['Content-Type'] = headers.get('Content-Type', 'application/json')
        loop = asyncio.get_event_loop()
        with aiohttp.ClientSession(loop=loop) as session:
            # be able to mock session from outside
            session = self.session or session
            resp = await session.post(
                url,
                params=params,
                headers=headers,
                data=_json.dumps(json),
            )
            return await resp.json()

    def get_app(self):
        if not self.has_app():
            loop = asyncio.get_event_loop()
            logger.debug('create web app')
            self.app = web.Application(
                loop=loop,
            )
        return self.app

    def has_app(self):
        return self.app is not None

    def webhook(self, uri, handler, token):
        logger.debug('register webhook {}'.format(uri))
        self.webhook_token = token
        self.get_app().router.add_get(uri, self.handle_webhook_validation)
        self.get_app().router.add_post(uri, WebhookHandler(handler).handle)

    def handle_webhook_validation(self, request):
        params = {name: value[0] for name, value in urllib.parse.parse_qs(request.query_string).items()}
        logger.debug('try to validate webhook with {}'.format(params))
        if params.get('hub.verify_token', None) == self.webhook_token and \
           params.get('hub.mode', None) == 'subscribe':
            return web.Response(text=params.get('hub.challenge'))
        else:
            return web.Response(text='Error, wrong validation token', status=HTTP_422_UNPROCESSABLE_ENTITY)

    async def start(self):
        if not self.has_app() or not self.auto_start:
            return
        logger.debug('start')
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
        if not self.has_app():
            return
        logger.debug('stop')
        self.server.close()
        await self.server.wait_closed()
        await self.app.shutdown()
        await self.handler.finish_connections(self.shutdown_timeout)
        await self.app.cleanup()
