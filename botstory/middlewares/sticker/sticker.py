from botstory import matchers
from botstory.ast import story_context
import logging

logger = logging.getLogger(__name__)


def get_sticker(ctx):
    return story_context.get_message_data(ctx, 'sticker_id')


ANY_LIKE = None
SMALL_LIKE = 369239263222822
MEDIUM_LIKE = 369239343222814
BIG_LIKE = 369239383222810

LIKE_STICKERS = (SMALL_LIKE, MEDIUM_LIKE, BIG_LIKE)


@matchers.matcher()
class Any:
    type = 'Sticker.Any'

    def __init__(self):
        pass

    def validate(self, ctx):
        return get_sticker(ctx)


@matchers.matcher()
class Like:
    type = 'Sticker.Like'

    def __init__(self, size=ANY_LIKE):
        if size == ANY_LIKE:
            self.valid_likes = LIKE_STICKERS
        else:
            self.valid_likes = [size]

    def validate(self, ctx):
        return get_sticker(ctx) in self.valid_likes

    def serialize(self):
        return self.option

    @staticmethod
    def deserialize(option):
        return Match(option)
