import aiohttp
import asyncio
import logging

from .middlewares.any import any
from .middlewares.location import location
from .middlewares.text import text

logger = logging.getLogger(__name__)
interfaces = {}

# temporal hack to be able hack web session from unit tests
web_session = None

async def ask(body, options=None, user=None):
    """
    simple ask with predefined options

    :param body:
    :param options: (optional)  in form of
    {'title': <message>, 'payload': <any json>}
    :param user:
    :return:
    """
    await send_text_message_to_all_interfaces(
        recipient=user, text=body, options=options, session=web_session)
    return any.Any()


# TODO: move to middlewares/location/location.py and make async

def ask_location(body, user):
    # TODO:
    # 1 ask user
    say(body, user)

    # 2 wait for answer
    # 3 process answer
    # 4 ask details once we not sure
    return [location.Any(), text.Any()]


async def say(body, user):
    """
    say something to user

    :param body:
    :param user:
    :return:
    """
    return await send_text_message_to_all_interfaces(
        recipient=user, text=body, session=web_session)


async def send_text_message_to_all_interfaces(*args, **kwargs):
    """
    TODO:
    we should know from where user has come and use right interface
    as well right interface can be chosen

    :param args:
    :param kwargs:
    :return:
    """
    logger.debug('async_send_text_message_to_all_interfaces')
    loop = asyncio.get_event_loop()
    with aiohttp.ClientSession(loop=loop) as session:
        # TODO: temporal hack to mock session
        kwargs = {'session': session, **kwargs,}
        # tasks = [interface.send_text_message(session=session, *args, **kwargs) for type, interface in
        tasks = [interface.send_text_message(*args, **kwargs) for type, interface in
                 interfaces.items()]

        logger.debug('tasks')
        logger.debug(tasks)

        res = [body for body in await asyncio.gather(*tasks)]
        logger.debug('  res')
        logger.debug(res)
        return res


def add_interface(interface):
    logger.debug('add_interface')
    logger.debug(interface)
    interfaces[interface.type] = interface
    return interface
