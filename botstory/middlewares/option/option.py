from botstory import matchers
from botstory.ast import story_context
import re


def get_option(ctx):
    return story_context.get_message_data(ctx, 'option', 'value')


@matchers.matcher()
class Any:
    type = 'Option.Any'

    def __init__(self):
        pass

    def validate(self, ctx):
        return get_option(ctx)


@matchers.matcher()
class Equal:
    type = 'Option.Equal'

    def __init__(self, option):
        self.option = option

    def validate(self, ctx):
        return get_option(ctx) == self.option

    def serialize(self):
        return self.option

    @staticmethod
    def deserialize(option):
        return Equal(option)


@matchers.matcher()
class Match:
    type = 'Option.Match'

    def __init__(self, pattern, flags=0):
        self.matcher = re.compile(pattern, flags=flags)

    def validate(self, ctx):
        option = get_option(ctx)
        if not option:
            return False

        matches = self.matcher.findall(option)
        if len(matches) == 0:
            return False

        story_context.set_message_data(ctx, 'option', 'matches', matches)
        return True

    def serialize(self):
        return {
            'pattern': self.matcher.pattern,
            'flags': self.matcher.flags,
        }


@matchers.matcher()
class OnStart:
    type = 'Option.OnStart'
    DEFAULT_OPTION_PAYLOAD = 'BOT_STORY.PUSH_GET_STARTED_BUTTON'

    def validate(self, ctx):
        return get_option(ctx) == self.DEFAULT_OPTION_PAYLOAD
