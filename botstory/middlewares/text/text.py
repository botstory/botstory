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
        return message.get('data', {}).get('text', {}).get('raw', None)


@matchers.matcher()
class Match:
    type = 'text.Match'

    def __init__(self, test_string):
        self.test_string = test_string

    def validate(self, message):
        return self.test_string == (message.get('data', {}).get('text', {}).get('raw', None))

    def serialize(self):
        return self.test_string

    def deserialize(self, state):
        self.test_string = state

    @staticmethod
    def can_handle(data):
        return utils.is_string(data)

    @staticmethod
    def handle(data):
        return Match(data)
