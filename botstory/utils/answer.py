from .. import story


def location(loc, session=None, user=None):
    return story.match_message({
        'location': loc,
        'session': session,
        'user': user
    })


def pure_text(text, session=None, user=None):
    return story.match_message({
        'text': {'raw': text},
        'session': session,
        'user': user
    })


def option(payload, session=None, user=None):
    return story.match_message({
        'option': payload,
        'session': session,
        'user': user
    })
