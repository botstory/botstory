import re
from ... import matchers, utils


@matchers.matcher()
class Any:
    """
    filter any raw text
    """
    type = 'text.Any'

    def __init__(self):
        pass

    def validate(self, message):
        return utils.safe_get(message, 'data', 'text', 'raw')


@matchers.matcher()
class Equal:
    """
    filter equal raw text (case sensitive)
    """
    type = 'text.Equal'

    def __init__(self, test_string):
        self.test_string = test_string

    def validate(self, message):
        return self.test_string == utils.safe_get(message, 'data', 'text', 'raw')

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

    def validate(self, message):
        return self.test_string == utils.safe_get(message, 'data', 'text', 'raw', default='').lower()

    def serialize(self):
        return self.test_string


@matchers.matcher()
class Match:
    type = 'text.Match'

    def __init__(self, pattern, flags=0):
        self.matcher = re.compile(pattern, flags=flags)

    def validate(self, message):
        matches = self.matcher.findall(utils.safe_get(message, 'data', 'text', 'raw'))
        if len(matches) == 0:
            return False
        message['data']['text']['matches'] = matches
        return True

    def serialize(self):
        return {
            'pattern': self.matcher.pattern,
            'flags': self.matcher.flags,
        }
