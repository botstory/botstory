from botstory import matchers, utils
from botstory.ast import story_context
import re


def get_text(ctx, default=None):
    return story_context.get_message_data(ctx, 'text', default=default)


def get_raw_text(ctx, default=None):
    return story_context.get_message_data(ctx, 'text', 'raw', default=default)


@matchers.matcher()
class Any:
    """
    filter any raw text
    """
    type = 'text.Any'

    def __init__(self):
        pass

    def validate(self, ctx):
        return get_raw_text(ctx)


@matchers.matcher()
class Equal:
    """
    filter equal raw text (case sensitive)
    """
    type = 'text.Equal'

    def __init__(self, test_string):
        self.test_string = test_string

    def validate(self, ctx):
        return get_raw_text(ctx) == self.test_string

    def serialize(self):
        return self.test_string

    @staticmethod
    def can_handle(data):
        return utils.is_string(data)

    @staticmethod
    def handle(data):
        return Equal(data)


@matchers.matcher()
class EqualCaseIgnore:
    """
    filter equal raw text (case in-sensitive)
    """
    type = 'text.EqualCaseIgnore'

    def __init__(self, test_string):
        self.test_string = test_string.lower()

    def validate(self, ctx):
        return get_raw_text(ctx, '').lower() == self.test_string

    def serialize(self):
        return self.test_string


@matchers.matcher()
class Match:
    type = 'text.Match'

    def __init__(self, pattern, flags=0):
        self.matcher = re.compile(pattern, flags=flags)

    def validate(self, ctx):
        matches = self.matcher.findall(get_raw_text(ctx))
        if len(matches) == 0:
            return False

        story_context.set_message_data(ctx, 'text', 'matches', matches)
        return True

    def serialize(self):
        return {
            'pattern': self.matcher.pattern,
            'flags': self.matcher.flags,
        }
