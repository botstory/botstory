from .middlewares.any.any import Any
from .integrations.fb import messanger


def ask(text, user):
    messanger.send_text_message(user.id, text=text)
    return Any()
