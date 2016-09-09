from .middlewares.any.any import Any
from .middlewares.text import text
from .middlewares.location import location
from .integrations.fb import messenger


def ask(text, user):
    say(text, user)
    return Any()


def ask_location(text, user):
    # TODO:
    # 1 ask user
    # 2 wait for answer
    # 3 process answer
    # 4 ask details once we not sure
    return [location.Any(), text.Any()]


def say(body, user):
    messenger.send_text_message(user.id, text=body)
