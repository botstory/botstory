from .. import story


def location(loc, user=None):
    return story.match_message({'location': loc, 'user': user})


def pure_text(text, user=None):
    return story.match_message({'text': {'raw': text}, 'user': user})
