import asyncio
import random

from .jsdict import JSDict


async def a_second():
    await asyncio.sleep(0.1)


def uniq_id():
    return random.randint(100000000, 123456789)


def build_fake_user():
    return {
        '_id': uniq_id(),
        'name': 'Alice',
        'slack_id': uniq_id(),
        'facebook_user_id': uniq_id(),
    }


def build_fake_session(user=None):
    user = user or {}
    return {
        'data': {},
        'stack': [],
        'facebook_user_id': user.get('facebook_user_id', uniq_id()),
        'user_id': user.get('_id', uniq_id()),
    }


def safe_get(dct, *keys, default=None):
    if dct is None:
        return None

    for key in keys:
        try:
            dct = dct[key]
        except (KeyError, TypeError):
            return default
    return dct


def safe_set(input_dict, *args):
    res = input_dict
    keys, last_key, value = args[:-2], args[-2], args[-1]
    keys_iter = iter(keys)
    try:
        key = None
        try:
            while True:
                key = next(keys_iter)
                res = res[key]
        except (KeyError, TypeError):
            while True:
                res[key] = {}
                res = res[key]
                key = next(keys_iter)
    except StopIteration:
        pass

    res[last_key] = value
    return input_dict


class SimpleTrigger:
    def __init__(self, value=None):
        self.is_triggered = False
        self.triggered_times = 0
        self.value = value

    def passed(self):
        self.is_triggered = True
        self.triggered_times += 1

    def is_passed(self):
        return self.is_triggered

    def inc(self):
        self.value += 1

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
