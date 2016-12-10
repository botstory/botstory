import asyncio
import logging

from . import chat, di
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

    di.injector.register(instance=middleware)
    di.bind(middleware, auto=True)

    # TODO: should use DI somehow
    if check_spec(['send_text_message'], middleware):
        chat.add_interface(middleware)

    return middleware


def clear(clear_library=True):
    """
    Clear all deps
    TODO: replace with DI

    :param clear_library:
    :return:
    """

    if clear_library:
        stories_library.clear()
    chat.clear()
    users.clear()

    global middlewares
    middlewares = []

    di.clear_instances()


def register():
    di.injector.register(instance=story_processor_instance)
    di.injector.register(instance=stories_library)
    di.injector.bind(story_processor_instance, auto=True)
    di.injector.bind(stories_library, auto=True)


async def setup(event_loop=None):
    register()
    await _do_for_each_extension('setup', event_loop)


async def start(event_loop=None):
    register()
    await _do_for_each_extension('start', event_loop)


async def stop(event_loop=None):
    await _do_for_each_extension('stop', event_loop)


async def _do_for_each_extension(command, even_loop):
    await asyncio.gather(
        *[getattr(m, command)() for m in middlewares if hasattr(m, command)],
        loop=even_loop)


def forever(loop):
    try:
        loop.run_forever()
    except KeyboardInterrupt:  # pragma: no cover
        pass
    finally:
        loop.run_until_complete(stop())


class Story:
    def on(self, receive):
        return on(receive)

    def part(self):
        return part()

    def callable(self):
        return callable()

    def case(self, default=forking.Undefined, equal_to=forking.Undefined, match=forking.Undefined):
        return case(default, equal_to, match)

    async def ask(self, body, options=None, user=None):
        return await chat.ask(body, options, user)

    async def say(self, body, user):
        return await chat.say(body, user)

    def use(self, middleware):
        return use(middleware)

    async def setup(self, event_loop=None):
        return await setup(event_loop)

    async def start(self, event_loop=None):
        return await start(event_loop)

    def clear(self):
        return clear()
