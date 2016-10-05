import asyncio
import random

from .jsdict import JSDict


async def a_second():
    await asyncio.sleep(0.1)


def uniq_id():
    return random.randint(100000000, 123456789)


def build_fake_user():
    return {
        'name': 'Alice',
        'slack_id': uniq_id(),
        'facebook_user_id': uniq_id(),
    }


def build_fake_session(user=None):
    user = user or {}
    return {
        'stack': [],
        'facebook_user_id': user.get('facebook_user_id', uniq_id()),
        'user_id': user.get('_id', uniq_id()),
    }


class SimpleTrigger:
    def __init__(self, value=None):
        self.is_triggered = False
        self.triggered_times = 0
        self.value = value

    def passed(self):
        self.is_triggered = True
        self.triggered_times += 1

    def receive(self, value):
        self.value = value

    def result(self):
        return self.value


def uniqify(seq, idfun=None):
    """
    remove duplicates

    get here https://www.peterbe.com/plog/uniqifiers-benchmark

    :param seq:
    :param idfun:
    :return:
    """
    # order preserving
    if idfun is None:
        def idfun(x): return x
    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        # in old Python versions:
        # if seen.has_key(marker)
        # but in new ones:
        if marker in seen: continue
        seen[marker] = 1
        result.append(item)
    return result


def is_string(obj):
    if isinstance(obj, str) or isinstance(obj, bytes) or isinstance(obj, bytearray):
        return True
    return False
