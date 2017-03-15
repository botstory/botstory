from botstory import matchers
from botstory.ast import story_context
import logging

logger = logging.getLogger(__name__)


def get_sticker(ctx):
    return story_context.get_message_data(ctx, 'sticker_id')


LIKE_STICKERS = ('369239383222810', '369239263222822', '369239343222814')


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

    def __init__(self):
        pass

    def validate(self, ctx):
        return get_sticker(ctx) in LIKE_STICKERS

    def serialize(self):
        return self.option

    @staticmethod
    def deserialize(option):
        return Match(option)
