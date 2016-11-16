import asyncio
import logging

from . import chat
from .ast import callable as callable_module, common, \
    forking, library, parser, processor, users

logger = logging.getLogger(__name__)

# instantiate handlers

stories_library = library.StoriesLibrary()

parser_instance = parser.Parser()

story_processor_instance = processor.StoryProcessor(
    parser_instance,
    stories_library,
    middlewares=[forking.Middleware()]
)

common_stories_instance = common.CommonStoriesAPI(
    parser_instance,
    stories_library)

callable_stories_instance = callable_module.CallableStoriesAPI(
    library=stories_library,
    parser_instance=parser_instance,
    processor_instance=story_processor_instance,
)

forking_api = forking.ForkingStoriesAPI(
    parser_instance=parser_instance,
)

# expose story API:

callable = callable_stories_instance.callable
case = forking_api.case
on = common_stories_instance.on
on_start = common_stories_instance.on_start
part = common_stories_instance.part

# expose message handler API:

match_message = story_processor_instance.match_message

# expose operators

EndOfStory = callable_module.EndOfStory
Switch = forking.Switch
SwitchOnValue = forking.SwitchOnValue


def check_spec(spec, obj):
    for method in [getattr(obj, s, None) for s in spec]:
        if not method:
            return False
    return True


middlewares = []


def use(middleware):
    """
    attache middleware

    :param middleware:
    :return:
    """

    logger.debug('use')
    logger.debug(middleware)

    middlewares.append(middleware)

    # TODO: maybe it is good time to start using DI (dependency injection)

    if check_spec(['send_text_message'], middleware):
        chat.add_interface(middleware)
        # TODO: should find more elegant way to inject library to fb interface
        # or information whether we have On Start story
        middleware.library = stories_library

    if check_spec(['handle'], middleware):
        story_processor_instance.add_interface(middleware)

    if check_spec(['get_user', 'set_user', 'get_session', 'set_session'], middleware):
        story_processor_instance.add_storage(middleware)

    if check_spec(['post', 'webhook'], middleware):
        chat.add_http(middleware)

    if middleware.type == 'interface.tracker':
        story_processor_instance.add_tracker(middleware)
        users.add_tracker(middleware)

    return middleware


def clear(clear_library=True):
    """
    Clear all deps
    TODO: replace with DI

    :param clear_library:
    :return:
    """

    story_processor_instance.clear()
    if clear_library:
        stories_library.clear()
    chat.clear()
    users.clear()

    global middlewares
    middlewares = []


async def setup():
    await _do_for_each_extension('setup')


async def start():
    await _do_for_each_extension('start')


async def stop():
    await _do_for_each_extension('stop')


async def _do_for_each_extension(command):
    await asyncio.gather(
        *[getattr(m, command)() for m in middlewares if hasattr(m, command)]
    )


def forever(loop):
    try:
        loop.run_forever()
    except KeyboardInterrupt:  # pragma: no cover
        pass
    finally:
        loop.run_until_complete(stop())
