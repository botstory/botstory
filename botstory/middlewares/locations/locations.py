from ... import matchers


def is_location(message):
    return message.get('location', False)


class Location:
    @matchers.matcher()
    class Any:
        def validate(self, message):
            return is_location(message)
