import asyncio

from ..story import match_message


async def a_second():
    await asyncio.sleep(0.1)


def match_pure_text(text, user=None):
    return match_message({'text': {'raw': text}, 'user': user})


class SimpleTrigger:
    def __init__(self):
        self.is_triggered = False

    def passed(self):
        self.is_triggered = True
