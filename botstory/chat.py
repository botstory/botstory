from .middlewares.any.any import Any
from .middlewares.text.text import Text
from .integrations.fb import messanger


def ask(text, user):
    messanger.send_text_message(user.id, text=text)
    return Any()


def ask_location(text, user):
    # TODO:
    # 1 ask user
    # 2 wait for answer
    # 3 process answer
    # 4 ask details once we not sure
    return Text.Any()
