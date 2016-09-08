from . import jsdict
from .. import story


def location(loc, user=None):
    return story.match_message(jsdict.JSDict({'location': loc, 'user': user}))


def pure_text(text, user=None):
    return story.match_message(jsdict.JSDict({'text': {'raw': text}, 'user': user}))
