from botstory.ast import stack_utils, story_context
import logging
from .. import matchers

logger = logging.getLogger(__name__)


@matchers.matcher()
class WaitForReturn:
    type = 'WaitForReturn'

    def __init__(self):
        pass

    def validate(self, message):
        # return 'return' in message
        return True


class EndOfStory:
    type = 'EndOfStory'

    def __init__(self, data={}):
        self.data = data


class CallableNodeWrapper:
    """
    helps start processing callable story
    """

    def __init__(self, ast_node, library, processor):
        self.library = library
        self.ast_node = ast_node
        self.processor = processor

    async def startpoint(self, *args, **kwargs):
        if len(args) > 0:
            parent_ctx = args[0]
            session = parent_ctx['session']
            user = parent_ctx['user']
        else:
            if {'session', 'user'} > set(kwargs):
                raise AttributeError('Got {} and {}. Should pass session as well'.format(args, kwargs))
            session = kwargs.pop('session')
            user = kwargs.pop('user')

        # we are going deeper so prepare one more item in stack
        logger.debug('  action: extend stack by +1')
        session = {
            **session,
            'data': kwargs,
            'stack': session['stack'] + [stack_utils.build_empty_stack_item(self.ast_node.topic)],
        }

        ctx = story_context.StoryContext(message={
            'session': session,
            # TODO: should get user from context
            'user': user,
        }, library=self.library)
        ctx = await self.processor.process_story(ctx)
        ctx = story_context.reducers.scope_out(ctx)

        logger.debug('# result of callable')
        logger.debug(ctx)

        if isinstance(ctx.waiting_for, EndOfStory):
            return ctx.waiting_for.data

        # because we would like to return to stories from caller
        # we should return our context to callee
        return ctx


class CallableStoriesAPI:
    def __init__(self, library, parser_instance, processor_instance):
        self.library = library
        self.parser_instance = parser_instance
        self.processor_instance = processor_instance

    def callable(self):
        def fn(callable_story):
            compiled_story = self.parser_instance.compile(
                callable_story,
            )
            self.library.add_callable(compiled_story)
            return CallableNodeWrapper(
                compiled_story,
                self.library,
                self.processor_instance,
            ).startpoint

        return fn
