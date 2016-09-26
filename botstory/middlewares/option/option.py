from ... import matchers


@matchers.matcher()
class Any:
    type = 'Option.Any'

    def __init__(self):
        pass

    def validate(self, message):
        return message.get('data', {}).get('option', False)
