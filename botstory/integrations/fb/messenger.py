import aiohttp
import asyncio


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

    def send_text_message(self, sender, text, options=None):
        # TODO: we won't use sync send text message
        pass

    async def async_send_text_message(self, recipient_id, text, options=None):
        """
        async send message to the facebook user (recipient)

        :param recipient_id:
        :param text:
        :param options:

        :return:
        """
        loop = asyncio.get_event_loop()
        with aiohttp.ClientSession(loop=loop) as session:
            # TODO: should use local session.
            # but use self.session to be able patch it from outside
            # for test purpose
            async with (self.session or session).post(
                    'https://graph.facebook.com/v2.6/me/messages/',
                    params={
                        'access_token': self.token,
                    },
                    data={
                        'recipient': {
                            'id': recipient_id,
                        },
                        'message': {
                            'text': text,
                        },
                    }) as resp:
                return await resp.json()
