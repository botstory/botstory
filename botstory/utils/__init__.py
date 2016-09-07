import asyncio

from ..story import match_message


class JSDict:
    def __init__(self, response):
        # don't use self.__dict__ here
        self._response = response

    def __getattr__(self, key):
        return self._response[key]


async def a_second():
    await asyncio.sleep(0.1)


def match_pure_text(text, user=None):
    return match_message(JSDict({'text': {'raw': text}, 'user': user}))


def build_fake_user():
    return JSDict({
        'id': 1234,
        'wait_for_message': None,
    })


class SimpleTrigger:
    def __init__(self):
        self.is_triggered = False

    def passed(self):
        self.is_triggered = True
