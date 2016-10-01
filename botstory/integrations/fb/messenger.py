import json


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

    async def send_text_message(self, session, recipient, text, options=[]):
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

        async with session.post(
                        self.api_uri + '/me/messages/',
                params={
                    'access_token': self.token,
                },
                headers={
                    'Content-Type': 'application/json'
                },
                data=json.dumps({
                    'recipient': {
                        'id': recipient.facebook_user_id,
                    },
                    'message': message,
                })) as resp:
            return await resp.json()
