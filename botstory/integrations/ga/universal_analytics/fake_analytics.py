"""
inspired by
https://github.com/KeepSafe/aiohttp/blob/master/examples/fake_server.py

"""

from aiohttp import web
import logging

from ...tests.fake_server import FakeServer, get, post

logger = logging.getLogger(__name__)


class FakeAnalytics(FakeServer):
    ROOT_URI = 'www.google-analytics.com'

    @get('/collect')
    async def on_me(self, request):
        return web.json_response({})

    @post('/collect')
    async def on_my_friends(self, request):
        return web.json_response({})
