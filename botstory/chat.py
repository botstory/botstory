from .middlewares.any import any.Any
from .middlewares.location import location
from .middlewares.text import text
from .integrations.fb import messenger


def ask(body, user):
    say(body, user)
    return any.Any()


def ask_location(body, user):
    # TODO:
    # 1 ask user
    say(body, user)

    # 2 wait for answer
    # 3 process answer
    # 4 ask details once we not sure
    return [location.Any(), text.Any()]


def say(body, user):
    messenger.send_text_message(user.id, text=body)
