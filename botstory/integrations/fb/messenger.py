import logging

logger = logging.getLogger(__file__)


class FBInterface:
    type = 'interface.facebook'

    def __init__(self,
                 api_uri='https://graph.facebook.com/v2.6',
                 token=None):
        """

        :param token: should take from os.environ['FB_ACCESS_TOKEN']
        """
        self.api_uri = api_uri
        self.token = token

        self.http = None
        self.processor = None
        self.storage = None

    async def send_text_message(self, recipient, text, options=[]):
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

    def add_storage(self, storage):
        logger.debug('add_storage')
        logger.debug(storage)
        self.storage = storage

    async def handle(self, entry):
        logger.debug('')
        logger.debug('> handle <')
        logger.debug('')
        logger.debug('  entry: {}'.format(entry))
        for e in entry:
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
                    user = await self.storage.new_user(
                        facebook_user_id=facebook_user_id,
                    )

                    """
                    Make request to facebook
                    to receive more information about user

                    curl -X GET "https://graph.facebook.com/v2.6/<USER_ID>?fields=first_name,last_name,profile_pic,locale,timezone,gender&access_token=PAGE_ACCESS_TOKEN"


                    "first_name": "Peter",
                    "last_name": Chang",
                    "profile_pic": "https://fbcdn-profile-a.akamaihd.net/hprofile-ak-xpf1/v/t1.0-1/p200x200/13055603_10105219398495383_8237637584159975445_n.jpg?oh=1d241d4b6d4dac50eaf9bb73288ea192&oe=57AF5C03&__gda__=1470213755_ab17c8c8e3a0a447fed3f272fa2179ce",
                    "locale": "en_US",
                    "timezone": -7,
                    "gender": "male"


                    More: https://developers.facebook.com/docs/messenger-platform/user-profile

                    """

                session = await self.storage.get_session(facebook_user_id=facebook_user_id)
                if not session:
                    logger.debug('  should create new session for user {}'.format(facebook_user_id))
                    session = await self.storage.new_session(
                        facebook_user_id=facebook_user_id,
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
