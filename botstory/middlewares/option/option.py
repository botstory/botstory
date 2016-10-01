from ... import matchers


@matchers.matcher()
class Any:
    type = 'Option.Any'

    def __init__(self):
        pass

    def validate(self, message):
        return message.get('data', {}).get('option', False)


@matchers.matcher()
class Match:
    type = 'Option.Match'

    def __init__(self, option):
        self.option = option

    def validate(self, message):
        return message.get('data', {}).get('option', None) == self.option

    def serialize(self):
        return self.option

    @staticmethod
    def deserialize(option):
        return Match(option)
