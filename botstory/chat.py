from .middlewares.any import any
from .middlewares.location import location
from .middlewares.text import text

interfaces = {}


def ask(body, options=None, user=None):
    """
    simple ask with predefined options

    :param body:
    :param options: (optional)  in form of
    {'title': <message>, 'payload': <any json>}
    :param user:
    :return:
    """
    send_text_message_to_all_interfaces(user.id, text=body, options=options)
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
    send_text_message_to_all_interfaces(user.id, text=body)


def send_text_message_to_all_interfaces(*args, **kwargs):
    # TODO we should know from where user has come and use right interface
    # as well right interface can be chosen
    for type, interface in interfaces.items():
        interface.send_text_message(*args, **kwargs)


def add_interface(interface):
    interfaces[interface.type] = interface
    return interface
