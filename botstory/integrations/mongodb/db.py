import logging
from motor import motor_asyncio

logger = logging.getLogger(__name__)


class MongodbInterface:
    """
    https://github.com/mongodb/motor
    """

    def __init__(self,
                 uri='localhost',
                 db_name='bots',
                 user_collection_name='user',
                 session_collection_name='session',
                 ):
        self.cx = None
        self.db = None
        self.session_collection = None
        self.user_collection = None
        self.uri = uri
        self.db_name = db_name
        self.session_collection_name = session_collection_name
        self.user_collection_name = user_collection_name

    async def connect(self, loop):
        self.cx = motor_asyncio.AsyncIOMotorClient(self.uri, io_loop=loop)
        self.db = self.cx.get_database(self.db_name)
        self.user_collection = self.db.get_collection(self.user_collection_name)
        self.session_collection = self.db.get_collection(self.session_collection_name)

    async def get_session(self, user_id):
        # TODO: should get from extensions
        return {}

    async def set_session(self, user_id, session):
        # TODO: should get from extensions
        pass

    async def get_user(self, user_id):
        return await self.user_collection.find_one({'_id': user_id})

    async def set_user(self, user):
        if not getattr(user, '_id', None):
            res = await self.user_collection.insert(user)
        else:
            res = await self.user_collection.update({'_id': user._id}, user)
        return res
