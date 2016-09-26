from ... import matchers


def is_location(message):
    return message.get('data', {}).get('location', False)


@matchers.matcher()
class Any:
    type = 'Location.Any'

    def __init__(self):
        pass

    def validate(self, message):
        return is_location(message)
