from botstory import di
from botstory.ast import story_context
from botstory.integrations import mocktracker

import logging

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

    async def match_message(self, message_ctx):
        """

        match bot message to existing stories
        and take into account context of current user

        :param message_ctx:
        :return: mutated message_ctx
        """
        logger.debug('')
        logger.debug('# match_message')
        logger.debug('')
        logger.debug(message_ctx)

        ctx = story_context.StoryContext(library=self.library,
                                         matched=False,
                                         message=message_ctx,
                                         )

        self.tracker.new_message(ctx)

        if ctx.is_empty_stack():
            if not ctx.does_it_match_any_story():
                # there is no stories for such message
                return ctx.message

            ctx = story_context.reducers.scope_in(ctx)
            ctx = await self.process_story(ctx)
            ctx = story_context.reducers.scope_out(ctx)

        while ctx.could_scope_out() and not ctx.is_empty_stack():
            logger.debug('# in a loop')
            logger.debug(ctx)

            # looking for first valid matcher
            while True:
                if ctx.is_empty_stack():
                    # we have reach the bottom of stack
                    if ctx.does_it_match_any_story():
                        # but sometimes we could jump on other global matcher
                        ctx = story_context.reducers.scope_in(ctx)
                        ctx = await self.process_story(ctx)
                        ctx = story_context.reducers.scope_out(ctx)
                        if ctx.is_empty_stack():
                            return ctx.message
                    else:
                        logger.debug('  we have reach the bottom of stack '
                                     'so no once has receive this message')
                        return ctx.message

                if ctx.is_scope_level() and \
                        (ctx.has_child_story() or ctx.matched) and \
                        not ctx.is_breaking_a_loop() or \
                                not ctx.is_scope_level() and \
                                not ctx.is_end_of_story():
                    # if we
                    # - haven't reach last step in list of story
                    # - isn't breaking a loop
                    # - inside of child scope and have matching sub-stories
                    # so we can parse result
                    break

                logger.debug('# tuning scope_out')
                ctx = story_context.reducers.scope_out(ctx)

            if ctx.has_child_story():
                ctx = story_context.reducers.scope_in(ctx)
            ctx = await self.process_story(ctx)
            logger.debug('# match_message scope_out')
            ctx = story_context.reducers.scope_out(ctx)

            if ctx.is_scope_level() and not ctx.is_breaking_a_loop():
                logger.debug('# the end of one story scope')
                break

        return ctx.message

    async def process_story(self, ctx):
        logger.debug('')
        logger.debug('# process_story')
        logger.debug('')
        logger.debug(ctx)

        if ctx.is_scope_level():
            return story_context.reducers.enter_new_scope(ctx)

        # integrate over parts of story
        last_story_part = None
        storyline = story_context.reducers.iterate_storyline(ctx)
        if not storyline:
            return ctx
        try:
            story_part_ctx = next(storyline)

            # loop thought storyline
            # we can't use for here because we should send update context
            # back to iterator
            while True:
                self.tracker.story(story_part_ctx)

                if story_part_ctx.has_child_story() or story_part_ctx.is_scope_level_part():
                    story_part_ctx = story_context.reducers.scope_in(story_part_ctx)
                    story_part_ctx = await self.process_story(story_part_ctx)
                    logger.debug('# process_story scope_out')
                    story_part_ctx = story_context.reducers.scope_out(story_part_ctx)
                else:
                    story_part_ctx = await story_context.reducers.execute(story_part_ctx)

                if story_part_ctx.is_waiting_for_input():
                    return story_part_ctx
                last_story_part = story_part_ctx
                story_part_ctx = storyline.send(story_part_ctx)
        except StopIteration:
            pass

        if last_story_part is None:
            logger.warn('# story line is empty or it is differ from what we have in stack')
            return ctx
        return last_story_part
