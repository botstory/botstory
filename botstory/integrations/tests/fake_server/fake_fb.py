"""
inspired by
https://github.com/KeepSafe/aiohttp/blob/master/examples/fake_server.py

"""

from aiohttp import web
import logging

from .server import FakeServer, get, post, delete

logger = logging.getLogger(__name__)

URI = 'https://graph.facebook.com{}'


class FakeFacebook(FakeServer):
    ROOT_URI = 'graph.facebook.com'

    @get('/v2.7/me')
    async def on_me(self, request):
        return web.json_response({
            "name": "John Doe",
            "id": "12345678901234567"
        })

    @get('/v2.7/me/friends')
    async def on_my_friends(self, request):
        return web.json_response({
            "data": [
                {
                    "name": "Bill Doe",
                    "id": "233242342342"
                },
                {
                    "name": "Mary Doe",
                    "id": "2342342343222"
                },
                {
                    "name": "Alex Smith",
                    "id": "234234234344"
                },
            ],
            "paging": {
                "cursors": {
                    "before": "QVFIUjRtc2c5NEl0ajN",
                    "after": "QVFIUlpFQWM0TmVuaDRad0dt",
                },
                "next": ("https://graph.facebook.com/v2.7/12345678901234567/"
                         "friends?access_token=EAACEdEose0cB")
            },
            "summary": {
                "total_count": 3
            }})

    @post('/v2.6/me/messages/')
    async def on_messages(self, request):
        return web.json_response({
            'status': 'ok',
        })

    @post('/v2.6/me/thread_settings')
    async def on_thread_settings_post(self, request):
        return web.json_response({
            'status': 'ok',
        })

    @delete('/v2.6/me/thread_settings')
    async def on_remove_thread_setting(self, request):
        return web.json_response({
            'status': 'ok',
        })
