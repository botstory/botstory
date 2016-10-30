class Invalid(BaseException):
    pass


class InvalidLength(Invalid):
    pass


def validate_greeting_text(message):
    if len(message) > 160:
        raise InvalidLength('greeting text should not exceed 160 length in characters')
