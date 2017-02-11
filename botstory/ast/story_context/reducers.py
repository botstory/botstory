from botstory import matchers
from botstory.ast import callable, stack_utils
import logging
import inspect

logger = logging.getLogger(__name__)


async def execute(ctx, story_part):
    waiting_for = story_part(ctx.message)
    if inspect.iscoroutinefunction(story_part):
        waiting_for = await waiting_for

    # TODO: don't mutate! should use reducer instead
    ctx.waiting_for = waiting_for
    return ctx


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

    logger.debug('# [>] going deeper')
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
        logger.debug('# [<] return')
        # TODO: !
        ctx.stack().pop()

    return ctx
