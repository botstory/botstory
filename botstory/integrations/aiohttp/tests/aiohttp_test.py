import pytest
from .. import AioHttpInterface
from ...fb.tests import fake_fb


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
