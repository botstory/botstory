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

    async def clear_collections(self):
        await self.session_collection.drop()
        self.session_collection = self.db.get_collection(self.session_collection_name)
        await self.user_collection.drop()
        self.user_collection = self.db.get_collection(self.user_collection_name)

    async def get_session(self, **kwargs):
        return await self.session_collection.find_one(kwargs)

    async def set_session(self, session):
        old_session = await self.session_collection.find_one({'user_id': session['user_id']})
        logger.debug('old_session')
        logger.debug(old_session)
        if not old_session:
            res = await self.session_collection.insert(session)
        else:
            res = await self.session_collection.update({'user_id': session['user_id']}, session)

        return res

    async def new_session(self, user, **kwargs):
        kwargs['user_id'] = kwargs.get('user_id', user['_id'])
        kwargs['stack'] = kwargs.get('stack', [])
        id = await self.session_collection.insert(kwargs)
        return await self.session_collection.find_one({'_id': id})

    async def get_user(self, **kwargs):
        if 'id' in kwargs:
            kwargs['_id'] = kwargs.get('id', None)
            del kwargs['id']
        return await self.user_collection.find_one(kwargs)

    async def set_user(self, user):
        if not getattr(user, '_id', None):
            res = await self.user_collection.insert(user)
        else:
            res = await self.user_collection.update({'_id': user._id}, user)
        return res

    async def new_user(self, **kwargs):
        id = await self.user_collection.insert(kwargs)
        return await self.user_collection.find_one({'_id': id})
