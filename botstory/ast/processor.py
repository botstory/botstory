from botstory import di, matchers
from botstory.ast import callable, forking, stack_utils
from botstory.integrations import mocktracker

import logging
import inspect

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
        if self.is_empty_stack():
            return self.library.get_global_story(self.message)
        else:
            return self.library.get_story_by_topic(self.stack_tail()['topic'], stack=self.stack()[:-1])

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
        logger.debug('> match_message <')
        logger.debug('')
        logger.debug('  {} '.format(message))

        ctx = StoryContext(message, self.library)

        self.tracker.new_message(
            user=message and message['user'],
            data=message['data'],
        )

        if ctx.is_empty_stack():
            if not ctx.does_it_match_any_story():
                # there is no stories for such message
                return None

            ctx = scope_in(ctx)

            # TODO: don't mutate! (should pass and get ctx)
            ctx.waiting_for = await self.process_story(
                message=ctx.message,
                compiled_story=ctx.compiled_story(),
            )

            ctx = scope_out(ctx)

        while not ctx.is_waiting_for_input() and not ctx.is_empty_stack():
            logger.debug('  session = {}'.format(message['session']))

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

                ctx = scope_out(ctx)

            if ctx.get_child_story():
                ctx = scope_in(ctx)

            # TODO: don't mutate! (should pass and get ctx)
            ctx.waiting_for = await self.process_story(
                message=ctx.message,
                compiled_story=ctx.compiled_story(),
            )

            ctx = scope_out(ctx)

        return ctx.waiting_for

    async def process_story(self, message, compiled_story,
                            story_args=[], story_kwargs={},
                            session=None,
                            ):
        logger.debug('')
        logger.debug('process_story')
        logger.debug('')

        logger.debug('! topic {}'.format(compiled_story.topic))
        logger.debug('  story {}'.format(compiled_story))
        logger.debug('  message {}'.format(message))

        if message:
            session = message['session']
        current_story = session['stack'][-1]
        start_step = current_story['step']
        step = start_step
        waiting_for = None
        story_line = compiled_story.story_line

        logger.debug('current_story {} ({})'.format(current_story, len(story_line)))

        # integrate over parts of story
        for step, story_part in enumerate(story_line[start_step:], start_step):
            logger.debug('')
            logger.debug('  next iteration of {}'.format(current_story['topic']))
            logger.debug('      step = {} ({})'.format(step, len(story_line)))
            logger.debug('      session {}'.format(session['stack']))

            current_story['step'] = step

            self.tracker.story(
                user=message and message['user'],
                story_name=current_story['topic'],
                story_part_name=story_part.__name__,
            )

            # check whether it could be new scope
            # TODO: it could be done at StoryPartFork.__call__
            if isinstance(story_part, forking.StoryPartFork):
                logger.debug('  it could be new scope')
                new_ctx_story = None

                if isinstance(waiting_for, forking.SwitchOnValue):
                    new_ctx_story = story_part.get_child_by_validation_result(waiting_for.value)

                if new_ctx_story:
                    self.build_new_scope(message['session']['stack'], new_ctx_story)
                    waiting_for = await self.process_story(
                        message=message,
                        compiled_story=new_ctx_story,
                    )
                    self.may_drop_scope(new_ctx_story, message['session']['stack'], waiting_for)
                    break

            logger.debug('  going to call: {}'.format(story_part.__name__))

            if message:
                # process common story part
                waiting_for = story_part(message)
            else:
                # process startpoint of callable story
                waiting_for = story_part(*story_args, **story_kwargs)

            if inspect.iscoroutinefunction(story_part):
                waiting_for = await waiting_for

            logger.debug('  got result {}'.format(waiting_for))

            if waiting_for and not isinstance(waiting_for, forking.SwitchOnValue):
                if isinstance(waiting_for, callable.EndOfStory):
                    if message:
                        message['data'] = {**message['data'], **waiting_for.data}
                else:
                    current_story['data'] = matchers.serialize(
                        matchers.get_validator(waiting_for)
                    )
                # should wait for new message income
                break

        current_story['step'] = step + 1

        return waiting_for

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
