import asyncio
import logging
from . import validate
from .. import commonhttp
from ...middlewares import option

logger = logging.getLogger(__name__)


class FBInterface:
    type = 'interface.facebook'

    def __init__(self,
                 api_uri='https://graph.facebook.com/v2.6',
                 greeting_text=None,
                 page_access_token=None,
                 persistent_menu=None,
                 webhook_url=None,
                 webhook_token=None,
                 ):
        """

        :param api_uri:
        :param greeting_text:
        :param page_access_token:
        :param persistent_menu:
        :param webhook_url:
        :param webhook_token:
        """
        self.api_uri = api_uri
        self.greeting_text = greeting_text
        self.persistent_menu = persistent_menu
        self.token = page_access_token
        self.webhook = webhook_url
        self.webhook_token = webhook_token

        self.library = None
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

        try:
            validate.send_text_message(text, options)
        except validate.Invalid as i:
            logger.warn(str(i))

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

        if self.greeting_text:
            asyncio.ensure_future(
                self.set_greeting_text(self.greeting_text)
            )

        if self.persistent_menu:
            asyncio.ensure_future(
                self.set_persistent_menu(self.persistent_menu)
            )

    def add_storage(self, storage):
        logger.debug('add_storage')
        logger.debug(storage)
        self.storage = storage

    async def request_profile(self, facebook_user_id):
        """
        Make request to facebook
        to receive more information about user

        More: https://developers.facebook.com/docs/messenger-platform/user-profile

        :param facebook_user_id:
        :return:
        """
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
        try:
            for e in data.get('entry', []):
                messaging = e.get('messaging', [])
                logger.debug('  messaging: {}'.format(messaging))

                if len(messaging) == 0:
                    logger.warning('  entry {} list lack of "messaging" field'.format(e))

                for m in messaging:
                    logger.debug('  m: {}'.format(m))

                    facebook_user_id = m['sender']['id']

                    logger.debug('before get user with facebook_user_id={}'.format(facebook_user_id))
                    user = await self.storage.get_user(facebook_user_id=facebook_user_id)
                    if not user:
                        logger.debug('  should create new user {}'.format(facebook_user_id))

                        try:
                            messenger_profile_data = await self.request_profile(facebook_user_id)
                            logger.debug('receive fb profile {}'.format(messenger_profile_data))
                        except commonhttp.errors.HttpRequestError as err:
                            logger.debug('fail on request fb profile of {}. with {}'.format(facebook_user_id, err))
                            messenger_profile_data = {
                                'no_fb_profile': True,
                            }

                        logger.debug('before creating new user')
                        user = await self.storage.new_user(
                            facebook_user_id=facebook_user_id,
                            no_fb_profile=messenger_profile_data.get('no_fb_profile', None),
                            first_name=messenger_profile_data.get('first_name', None),
                            last_name=messenger_profile_data.get('last_name', None),
                            profile_pic=messenger_profile_data.get('profile_pic', None),
                            locale=messenger_profile_data.get('locale', None),
                            timezone=messenger_profile_data.get('timezone', None),
                            gender=messenger_profile_data.get('gender', None),
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

                    if 'message' in m:
                        logger.debug('message notification')
                        raw_message = m.get('message', {})
                        if 'is_echo' in raw_message:
                            # TODO: should react somehow.
                            # for example storing for debug purpose
                            logger.debug('just echo message')
                        else:
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

                    elif 'postback' in m:
                        message['data'] = {
                            'option': m['postback']['payload'],
                        }
                        await self.processor.match_message(message)
                    elif 'delivery' in m:
                        logger.debug('delivery notification')
                    elif 'read' in m:
                        logger.debug('read notification')
                    else:
                        logger.warning('(!) unknown case {}'.format(e))

        except BaseException as err:
            logger.exception(err)

        return {
            'status': 200,
            'text': 'Ok!',
        }

    async def start(self):
        logger.debug('start')

        # check whether we have `On Start Story`
        have_on_start_story = not not self.library.get_right_story({
            'data': {'option': option.OnStart.DEFAULT_OPTION_PAYLOAD}
        })
        if have_on_start_story:
            await self.set_greeting_call_to_action_payload(option.OnStart.DEFAULT_OPTION_PAYLOAD)

    async def set_greeting_text(self, message):
        """
        set a greeting for new conversations

        can use for personalizing
            {{user_first_name}}
            {{user_last_name}}
            {{user_full_name}}

        more: https://developers.facebook.com/docs/messenger-platform/thread-settings/greeting-text

        :param message:
        :return:
        """
        try:
            validate.greeting_text(message)
        except validate.Invalid as i:
            logger.warn(str(i))

        self.greeting_text = message

        if not self.http:
            # should wait until receive http
            return

        await self.http.post(
            self.api_uri + '/me/thread_settings',
            params={
                'access_token': self.token,
            },
            json={
                'setting_type': 'greeting',
                'greeting': {
                    'text': message,
                },
            }
        )

    async def remove_greeting_text(self):
        await self.http.delete(
            self.api_uri + '/me/thread_settings',
            params={
                'access_token': self.token,
            },
            json={
                'setting_type': 'greeting',
            }
        )

    async def set_greeting_call_to_action_payload(self, payload):
        """

        more: https://developers.facebook.com/docs/messenger-platform/thread-settings/get-started-button

        :param payload:
        :return:
        """
        await self.http.post(
            self.api_uri + '/me/thread_settings',
            params={
                'access_token': self.token,
            },
            json={
                'setting_type': 'call_to_actions',
                'thread_state': 'new_thread',
                'call_to_actions': [{'payload': payload}]
            }
        )

    async def remove_greeting_call_to_action_payload(self):
        await self.http.delete(
            self.api_uri + '/me/thread_settings',
            params={
                'access_token': self.token,
            },
            json={
                'setting_type': 'call_to_actions',
                'thread_state': 'new_thread',
            }
        )

    async def set_persistent_menu(self, menu):
        """
        more: https://developers.facebook.com/docs/messenger-platform/thread-settings/persistent-menu

        :param menu:
        :return:
        """
        try:
            validate.persistent_menu(menu)
        except validate.Invalid as i:
            logger.warn(str(i))

        self.persistent_menu = menu

        if not self.http:
            # should wait until receive http
            return

        await self.http.post(
            self.api_uri + '/me/thread_settings',
            params={
                'access_token': self.token,
            },
            json={
                'setting_type': 'call_to_actions',
                'thread_state': 'new_thread',
                'call_to_actions': menu
            }
        )

    async def remove_persistent_menu(self):
        await self.http.delete(
            self.api_uri + '/me/thread_settings',
            params={
                'access_token': self.token,
            },
            json={
                'setting_type': 'call_to_actions',
                'thread_state': 'new_thread',
            }
        )
