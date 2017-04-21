import asyncio
import logging
from motor import motor_asyncio
from ... import di

logger = logging.getLogger(__name__)


@di.desc('storage', reg=False)
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

    async def start(self):
        loop = asyncio.get_event_loop()
        logger.debug('start')
        self.cx = motor_asyncio.AsyncIOMotorClient(self.uri, io_loop=loop)
        logger.debug(' create client for: {}'.format(self.uri))
        self.db = self.cx.get_database(self.db_name)
        logger.debug(' get db: {}'.format(self.db_name))
        self.session_collection = self.db.get_collection(self.session_collection_name)
        logger.debug(' get session collection: {}'.format(self.session_collection_name))
        self.user_collection = self.db.get_collection(self.user_collection_name)
        logger.debug(' get user collection: {}'.format(self.user_collection_name))

    async def stop(self):
        self.cx = None
        self.db = None
        self.session_collection = None
        self.user_collection = None

    async def clear_collections(self):
        await self.session_collection.drop()
        self.session_collection = self.db.get_collection(self.session_collection_name)
        await self.user_collection.drop()
        self.user_collection = self.db.get_collection(self.user_collection_name)

    async def get_session(self, **kwargs):
        session = await self.session_collection.find_one(kwargs)
        if not session:
            return None
        session.pop('lastModified', None)
        return session

    async def set_session(self, session):
        logger.info('set_session {}'.format(session))
        if '_id' in session:
            _id = session['_id']
            session.pop('lastModified', None)
            res = await self.session_collection.update_one(
                {'_id': _id},
                {
                    '$set': session,
                    '$currentDate': {
                        'lastModified': True
                    },
                },
            )

            if res.matched_count != 0:
                return _id

        return await self.session_collection.insert(session)

    async def new_session(self, user, **kwargs):
        logger.info('new_session for {}'.format(user))
        kwargs['user_id'] = kwargs.get('user_id', user['_id'])
        kwargs['stack'] = kwargs.get('stack', [])
        _id = await self.session_collection.insert(kwargs)
        return await self.session_collection.find_one({'_id': _id})

    async def get_user(self, **kwargs):
        if 'id' in kwargs:
            kwargs['_id'] = kwargs.get('id', None)
            del kwargs['id']
        user = await self.user_collection.find_one(kwargs)
        if not user:
            return None
        user.pop('lastModified', None)
        return user

    async def set_user(self, user):
        logger.info('set_user {}'.format(user))
        if '_id' in user:
            _id = user['_id']
            user.pop('lastModified', None)
            res = await self.user_collection.update_one(
                {'_id': _id},
                {
                    '$set': user,
                    '$currentDate': {
                        'lastModified': True
                    },
                },
            )
            if res.matched_count != 0:
                return _id
        return await self.user_collection.insert(user)

    # TODO: should be able to process dictionary
    async def new_user(self, **kwargs):
        logger.debug('store new user {}'.format(kwargs))
        _id = await self.user_collection.insert(kwargs)
        return await self.user_collection.find_one({'_id': _id})
