import asyncio
import logging

from . import chat, di
from .ast import callable as callable_module, common, \
    forking, library, loop, parser, processor, users

logger = logging.getLogger(__name__)


def check_spec(spec, obj):
    for method in [getattr(obj, s, None) for s in spec]:
        if not method:
            return False
    return True


class Story:
    def __init__(self):
        self.stories_library = library.StoriesLibrary()

        self.parser_instance = parser.Parser(self.stories_library)

        self.story_processor_instance = processor.StoryProcessor(
            self.parser_instance,
            self.stories_library,
        )

        self.match_message = self.story_processor_instance.match_message

        self.callable_stories_instance = callable_module.CallableStoriesAPI(
            library=self.stories_library,
            parser_instance=self.parser_instance,
            processor_instance=self.story_processor_instance,
        )
        self.common_stories_instance = common.CommonStoriesAPI(
            self.parser_instance,
            self.stories_library)
        self.forking_api = forking.ForkingStoriesAPI(
            parser_instance=self.parser_instance,
        )
        self.story_loop = loop.StoryLoopAPI(
            library=self.stories_library,
            parser_instance=self.parser_instance,
        )
        self.middlewares = []
        self.chat = chat.Chat()
        self.users = users.Users()

    # Facade
    def loop(self):
        """
        close loop/scope of sub-stories
        :return:
        """
        return self.story_loop.loop()

    def on(self, receive):
        return self.common_stories_instance.on(receive)

    def on_start(self):
        return self.common_stories_instance.on_start()

    def part(self):
        return self.common_stories_instance.part()

    def callable(self):
        return self.callable_stories_instance.callable()

    def case(self, default=forking.Undefined, equal_to=forking.Undefined, match=forking.Undefined):
        return self.forking_api.case(default, equal_to, match)

    async def ask(self, body, options=None, user=None):
        return await self.chat.ask(body, options, user)

    async def say(self, body, user, options=None):
        return await self.chat.say(body, user, options)

    def use(self, middleware):
        """
        attache middleware

        :param middleware:
        :return:
        """

        logger.debug('use')
        logger.debug(middleware)

        self.middlewares.append(middleware)

        di.injector.register(instance=middleware)
        di.bind(middleware, auto=True)

        # TODO: should use DI somehow
        if check_spec(['send_text_message'], middleware):
            self.chat.add_interface(middleware)

        return middleware

    async def setup(self, event_loop=None):
        self.register()
        return await self._do_for_each_extension('setup', event_loop)

    async def start(self, event_loop=None):
        self.register()
        await self._do_for_each_extension('before_start', event_loop)
        await self._do_for_each_extension('start', event_loop)
        await self._do_for_each_extension('after_start', event_loop)

    async def stop(self, event_loop=None):
        return await self._do_for_each_extension('stop', event_loop)

    def forever(self, loop):
        try:
            loop.run_forever()
        except KeyboardInterrupt:  # pragma: no cover
            pass
        finally:
            loop.run_until_complete(self.stop())

    def register(self):
        di.injector.register(instance=self.parser_instance)
        di.injector.register(instance=self.story_processor_instance)
        di.injector.register(instance=self.stories_library)
        di.injector.register(instance=self.users)
        di.injector.bind(self.parser_instance, auto=True)
        di.injector.bind(self.story_processor_instance, auto=True)
        di.injector.bind(self.stories_library, auto=True)
        di.injector.bind(self.users, auto=True)

    async def _do_for_each_extension(self, command, even_loop):
        await asyncio.gather(
            *[getattr(m, command)() for m in self.middlewares if hasattr(m, command)],
            loop=even_loop)

    def clear(self):
        """
        Clear all deps
        TODO: replace with DI

        :return:
        """

        di.clear_instances()
