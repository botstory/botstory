import logging

logger = logging.getLogger(__name__)


class FBInterface:
    type = 'interface.facebook'

    def __init__(self,
                 api_uri='https://graph.facebook.com/v2.6',
                 page_access_token=None,
                 webhook_url=None,
                 webhook_token=None,
                 ):
        """

        :param api_uri:
        :param page_access_token:
        :param webhook_url:
        :param webhook_token:
        """
        self.api_uri = api_uri
        self.token = page_access_token
        self.webhook = webhook_url
        self.webhook_token = webhook_token

        self.http = None
        self.processor = None
        self.storage = None

    async def send_text_message(self, recipient, text, options=None):
        """
        async send message to the facebook user (recipient)

        :param session:
        :param recipient:
        :param text:
        :param options:

        :return:
        """

        if not options:
            options = []

        message = {
            'text': text,
        }

        quick_replies = [{**reply, 'content_type': 'text'} for reply in options]
        if len(quick_replies) > 0:
            message['quick_replies'] = quick_replies

        return await self.http.post(
            self.api_uri + '/me/messages/',
            params={
                'access_token': self.token,
            },
            json={
                'recipient': {
                    'id': recipient['facebook_user_id'],
                },
                'message': message,
            })

    def add_http(self, http):
        logger.debug('add_http')
        logger.debug(http)
        self.http = http
        if self.webhook:
            http.webhook(self.webhook, self.handle, self.webhook_token)

    def add_storage(self, storage):
        logger.debug('add_storage')
        logger.debug(storage)
        self.storage = storage

    async def request_profile(self, facebook_user_id):
        return await self.http.get(
            '{}/{}'.format(self.api_uri, facebook_user_id),
            params={
                'access_token': self.token,
            },
        )

    async def handle(self, data):
        logger.debug('')
        logger.debug('> handle <')
        logger.debug('')
        logger.debug('  entry: {}'.format(data))
        for e in data.get('entry', []):
            messaging = e.get('messaging', [])
            logger.debug('  messaging: {}'.format(messaging))

            if len(messaging) == 0:
                logger.warning('  entry {} list lack of "messaging" field'.format(e))

            for m in messaging:
                logger.debug('  m: {}'.format(m))

                facebook_user_id = m['sender']['id']

                user = await self.storage.get_user(facebook_user_id=facebook_user_id)
                if not user:
                    logger.debug('  should create new user {}'.format(facebook_user_id))

                    """
                    Make request to facebook
                    to receive more information about user

                    More: https://developers.facebook.com/docs/messenger-platform/user-profile
                    """
                    messager_profile_data = await self.request_profile(facebook_user_id)

                    user = await self.storage.new_user(
                        facebook_user_id=facebook_user_id,
                        first_name=messager_profile_data.get('first_name', None),
                        last_name=messager_profile_data.get('last_name', None),
                        profile_pic=messager_profile_data.get('profile_pic', None),
                        locale=messager_profile_data.get('locale', None),
                        timezone=messager_profile_data.get('timezone', None),
                        gender=messager_profile_data.get('gender', None),
                    )

                session = await self.storage.get_session(facebook_user_id=facebook_user_id)
                if not session:
                    logger.debug('  should create new session for user {}'.format(facebook_user_id))
                    session = await self.storage.new_session(
                        facebook_user_id=facebook_user_id,
                        stack=[],
                        user=user,
                    )

                message = {
                    'session': session,
                    'user': user,
                }
                raw_message = m.get('message', {})

                if raw_message == {}:
                    logger.warning('  entry {} "message" field is empty'.format(e))

                logger.debug('  raw_message: {}'.format(raw_message))

                data = {}
                text = raw_message.get('text', None)
                if text is not None:
                    data['text'] = {
                        'raw': text,
                    }
                else:
                    logger.warning('  entry {} "text"'.format(e))

                quick_reply = raw_message.get('quick_reply', None)
                if quick_reply is not None:
                    data['option'] = quick_reply['payload']

                message['data'] = data

                await self.processor.match_message(message)
