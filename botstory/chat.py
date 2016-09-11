from .middlewares.any import any
from .middlewares.location import location
from .middlewares.text import text
from .integrations.fb import messenger


def ask(body, options=None, user=None):
    """
    simple ask with predefined options

    :param body:
    :param options: (optional)  in form of
    {'title': <message>, 'payload': <any json>}
    :param user:
    :return:
    """
    messenger.send_text_message(user.id, text=body, options=options)
    return any.Any()


# TODO: move to middlewares/location/location.py

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
