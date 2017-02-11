from botstory import matchers
from botstory.ast import callable, stack_utils

import logging

logger = logging.getLogger(__name__)


class StoryContext:
    def __init__(self, message, library):
        self.library = library
        self.message = message
        self.waiting_for = None

    def is_empty_stack(self):
        return len(self.stack()) == 0

    def is_waiting_for_input(self):
        return self.waiting_for and \
               not isinstance(self.waiting_for, callable.EndOfStory)

    def compiled_story(self):
        logger.debug('def compiled_story(self):')
        logger.debug('self.is_empty_stack()')
        logger.debug(self.is_empty_stack())
        logger.debug('self.stack()')
        logger.debug(self.stack())
        if self.is_empty_stack():
            return self.library.get_global_story(self.message)
        else:
            res = self.library.get_story_by_topic(self.stack_tail()['topic'], stack=self.stack()[:-1])
            logger.debug('res')
            logger.debug(type(res))
            logger.debug(res)
            return res

    def stack(self):
        return self.message['session']['stack']

    def stack_tail(self):
        return self.stack()[-1]

    def is_end_of_story(self):
        return self.stack_tail()['step'] >= len(self.compiled_story().story_line)

    def does_it_match_any_story(self):
        return self.compiled_story() is not None

    def is_tail_of_story(self):
        return self.stack_tail()['step'] >= len(self.compiled_story().story_line) - 1

    def get_child_story(self):
        """
        try child story that match message and get scope of it
        :return:
        """
        stack_tail = self.stack_tail()
        validator = matchers.deserialize(stack_tail['data'])

        story_part = self.compiled_story().story_line[stack_tail['step']]

        validation_result = validator.validate(self.message)

        if hasattr(story_part, 'get_child_by_validation_result'):
            return story_part.get_child_by_validation_result(validation_result)
        else:
            return None


# Context Reducers

# TODO: should make it immutable
def scope_in(ctx):
    """
    - build new scope on the top of stack
    - and current scope will wait for it result

    :param ctx:
    :return:
    """
    compiled_story = None
    if not ctx.is_empty_stack():
        compiled_story = ctx.get_child_story()
        # TODO: ! use reduceer
        last_stack_item = ctx.stack_tail()
        last_stack_item['step'] += 1
        last_stack_item['data'] = matchers.serialize(callable.WaitForReturn())

    if not compiled_story:
        compiled_story = ctx.compiled_story()

    logger.debug('[>] going deeper')
    # TODO: ! use reduceer
    stack = ctx.stack()
    stack.append(stack_utils.build_empty_stack_item(compiled_story.topic))

    return ctx


# TODO: should make it immutable
def scope_out(ctx):
    """
    drop last stack item if we have reach the end of stack
    and don't wait any input

    :param ctx:
    :return:
    """
    # we reach the end of story line
    # so we could collapse previous scope and related stack item
    if ctx.is_tail_of_story() and not ctx.is_waiting_for_input():
        logger.debug('[<] return')
        # TODO: !
        ctx.stack().pop()

    return ctx
