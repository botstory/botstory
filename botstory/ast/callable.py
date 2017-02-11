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


def process_end_of_story(message, waiting_for):
    logger.debug('  got EndOfStory!')
    if message:
        message['data'] = {**message['data'], **waiting_for.data}
    return waiting_for


class CallableNodeWrapper:
    """
    helps start processing callable story
    """

    def __init__(self, ast_node, library, processor_instance):
        self.library = library
        self.ast_node = ast_node
        self.processor_instance = processor_instance

    async def startpoint(self, *args, **kwargs):
        if 'session' not in kwargs:
            raise AttributeError('Got {} and {}. Should pass session as well'.format(args, kwargs))

        # TODO: get session from context
        session = kwargs.pop('session')

        # we are going deeper so prepare one more item in stack
        logger.debug('  action: extend stack by +1')
        session['stack'].append(stack_utils.build_empty_stack_item(self.ast_node.topic))
        ctx = story_context.StoryContext(message={
            'session': session,
            # TODO: get user from context
            'user': kwargs.pop('user'),
            'data': kwargs,
        }, library=self.library)
        ctx = await self.processor_instance.process_story(ctx=ctx,
                                                          # session=session,
                                                          # we don't have message yet
                                                          # TODO: 1st it should be context
                                                          # and it should be ever for callable
                                                          # message=None,
                                                          # compiled_story=self.ast_node,
                                                          )

        ctx = story_context.scope_out(ctx)

        if isinstance(ctx.waiting_for, EndOfStory):
            return ctx.waiting_for.data
        return ctx.waiting_for


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
