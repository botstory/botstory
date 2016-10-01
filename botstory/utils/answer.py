from .. import story


async def location(loc, session=None, user=None):
    return await story.match_message({
        'data': {
            'location': loc,
        },
        'session': session,
        'user': user
    })


async def pure_text(text, session=None, user=None):
    return await story.match_message({
        'data': {
            'text': {'raw': text},
        },
        'session': session,
        'user': user
    })


async def option(payload, session=None, user=None):
    return await story.match_message({
        'data': {
            'option': payload,
        },
        'session': session,
        'user': user
    })
