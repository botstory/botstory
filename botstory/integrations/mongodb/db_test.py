import pytest

from . import db
from ... import utils


@pytest.mark.asyncio
async def test_store_restore_user(event_loop):
    db_interface = db.MongodbInterface(uri='mongo', db_name='test')
    await db_interface.connect(loop=event_loop)
    user = utils.build_fake_user()

    user_id = await db_interface.set_user(user._response)
    restored_user = await db_interface.get_user(user_id)

    assert user.items() == restored_user.items()
