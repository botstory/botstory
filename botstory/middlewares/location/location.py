from botstory import matchers
from botstory.ast import story_context


def get_location(ctx):
    return story_context.get_message_data(ctx, 'location')


@matchers.matcher()
class Any:
    type = 'Location.Any'

    def __init__(self):
        pass

    def validate(self, ctx):
        return get_location(ctx)
