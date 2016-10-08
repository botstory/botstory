import aiohttp
import asyncio
import logging
import json as _json

logger = logging.getLogger(__name__)


class AioHttpInterface:
    type = 'interface.aiohttp'

    def __init__(self, port=None, loop=None):
        self.session = None
        self.loop = loop or asyncio.get_event_loop()

    async def post(self, url, params=None, headers=None, json=None):
        logger.debug('post url={}'.format(url))
        headers = headers or {}
        headers['Content-Type'] = headers.get('Content-Type', 'application/json')
        with aiohttp.ClientSession(loop=self.loop) as session:
            # be able to mock session from outside
            session = self.session or session
            resp = await session.post(url,
                                      params=params,
                                      headers=headers,
                                      data=_json.dumps(json)
                                      )
            return await resp.json()
