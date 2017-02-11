from botstory import di, matchers
from botstory.ast import callable, forking, stack_utils, story_context
from botstory.integrations import mocktracker

import logging
import inspect

logger = logging.getLogger(__name__)


@di.desc(reg=False)
class StoryProcessor:
    def __init__(self, parser_instance, library):
        self.library = library
        self.parser_instance = parser_instance
        self.tracker = mocktracker.MockTracker()

    @di.inject()
    def add_tracker(self, tracker):
        logger.debug('add_tracker')
        logger.debug(tracker)
        if not tracker:
            return
        self.tracker = tracker

    async def match_message(self, message):
        """

        match bot message to existing stories
        and take into account context of current user

        :param message:
        :return:
        """
        logger.debug('')
        logger.debug('# match_message')
        logger.debug('')
        logger.debug(message)

        ctx = story_context.StoryContext(message, self.library)

        self.tracker.new_message(
            user=message and message['user'],
            data=message['data'],
        )

        if ctx.is_empty_stack():
            if not ctx.does_it_match_any_story():
                # there is no stories for such message
                return None

            ctx = story_context.scope_in(ctx)

            ctx = await self.process_story(ctx)

            ctx = story_context.scope_out(ctx)

        while not ctx.is_waiting_for_input() and not ctx.is_empty_stack():
            logger.debug('# in a loop')
            logger.debug(ctx)

            # looking for first valid matcher
            while True:
                if ctx.is_empty_stack():
                    # we have reach the bottom of stack
                    logger.debug('  we have reach the bottom of stack '
                                 'so no once has receive this message')
                    return None

                if not ctx.is_end_of_story():
                    # if we haven't reach last step in list of story so we can parse result
                    break

                ctx = story_context.scope_out(ctx)

            if ctx.get_child_story():
                ctx = story_context.scope_in(ctx)

            ctx = await self.process_story(ctx)

            ctx = story_context.scope_out(ctx)

        return ctx.waiting_for

    async def process_story(self, ctx):
        logger.debug('')
        logger.debug('# process_story')
        logger.debug('')
        logger.debug(ctx)

        message = ctx.message
        compiled_story = ctx.compiled_story()

        session = message['session']
        current_story = session['stack'][-1]
        start_step = current_story['step']
        step = start_step
        waiting_for = None
        story_line = compiled_story.story_line

        # integrate over parts of story
        for step, story_part in enumerate(story_line[start_step:], start_step):
            logger.debug('# in a loop')
            logger.debug(ctx)

            current_story['step'] = step

            self.tracker.story(
                user=message and message['user'],
                story_name=current_story['topic'],
                story_part_name=story_part.__name__,
            )

            # check whether it could be new scope
            # TODO: it could be done at StoryPartFork.__call__
            if isinstance(story_part, forking.StoryPartFork):
                child_story = None

                if isinstance(waiting_for, forking.SwitchOnValue):
                    child_story = story_part.get_child_by_validation_result(waiting_for.value)

                if child_story:
                    # TODO: don't mutate! should use reducer instead
                    ctx.waiting_for = waiting_for
                    # ctx = story_context.scope_in(ctx)
                    self.build_new_scope(message['session']['stack'], child_story)

                    ctx = await self.process_story(ctx)
                    waiting_for = ctx.waiting_for
                    # ctx = story_context.scope_out(ctx)
                    self.may_drop_scope(child_story, message['session']['stack'], waiting_for)
                    break

            logger.debug('#  going to call: {}'.format(story_part.__name__))

            waiting_for = story_part(message)

            if inspect.iscoroutinefunction(story_part):
                waiting_for = await waiting_for

            logger.debug('#  got result {}'.format(waiting_for))

            if waiting_for and not isinstance(waiting_for, forking.SwitchOnValue):
                if isinstance(waiting_for, callable.EndOfStory):
                    if message:
                        if isinstance(waiting_for.data, dict):
                            message['data'] = {**message['data'], **waiting_for.data}
                        else:
                            message['data'] = waiting_for.data
                else:
                    current_story['data'] = matchers.serialize(
                        matchers.get_validator(waiting_for)
                    )
                # should wait for new message income
                break

        current_story['step'] = step + 1

        # TODO: don't mutate! should use reducer instead
        ctx.waiting_for = waiting_for
        return ctx

    def build_new_scope(self, stack, new_ctx_story):
        """
        - build new scope on the top of stack
        - and current scope will wait for it result

        :param stack:
        :param new_ctx_story:
        :return:
        """
        if len(stack) > 0:
            last_stack_item = stack[-1]
            last_stack_item['step'] += 1
            last_stack_item['data'] = matchers.serialize(callable.WaitForReturn())

        logger.debug('[>] going deeper')
        stack.append(stack_utils.build_empty_stack_item(
            new_ctx_story.topic
        ))

    def may_drop_scope(self, compiled_story, stack, waiting_for):
        # we reach the end of story line
        # so we could collapse previous scope and related stack item
        if stack[-1]['step'] >= len(compiled_story.story_line) - 1 and not waiting_for:
            logger.debug('[<] return')
            stack.pop()
