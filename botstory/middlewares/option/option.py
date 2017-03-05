from botstory.ast import story_context
from ... import matchers


def get_option(ctx):
    return story_context.get_message_data(ctx, 'option')


@matchers.matcher()
class Any:
    type = 'Option.Any'

    def __init__(self):
        pass

    def validate(self, ctx):
        return get_option(ctx)


@matchers.matcher()
class Match:
    type = 'Option.Match'

    def __init__(self, option):
        self.option = option

    def validate(self, ctx):
        return get_option(ctx) == self.option

    def serialize(self):
        return self.option

    @staticmethod
    def deserialize(option):
        return Match(option)


@matchers.matcher()
class OnStart:
    type = 'Option.OnStart'
    DEFAULT_OPTION_PAYLOAD = 'BOT_STORY.PUSH_GET_STARTED_BUTTON'

    def validate(self, ctx):
        return get_option(ctx) == self.DEFAULT_OPTION_PAYLOAD
