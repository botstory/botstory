import logging
import inspect

from botstory.ast import stack_utils
from . import parser, callable, forking
from .. import di, matchers
from ..integrations import mocktracker

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
        logger.debug('> match_message <')
        logger.debug('')
        logger.debug('  {} '.format(message))

        self.tracker.new_message(
            user=message and message['user'],
            data=message['data'],
        )

        stack = message['session']['stack']

        waiting_for = None

        if len(stack) == 0:
            compiled_story = self.library.get_global_story(message)
            if not compiled_story:
                # there is no stories for such message
                return None

            self.build_new_scope(stack, compiled_story)

            waiting_for = await self.process_story(
                message=message,
                compiled_story=compiled_story,
            )

            self.may_drop_scope(compiled_story, stack, waiting_for)

        while (not waiting_for or isinstance(waiting_for, callable.EndOfStory)) and len(stack) > 0:
            logger.debug('  session = {}'.format(message['session']))

            # looking for first valid matcher
            while True:
                if len(stack) == 0:
                    # we have reach the bottom of stack
                    logger.debug('  we have reach the bottom of stack '
                                 'so no once has receive this message')
                    return None

                stack_tail = stack[-1]
                compiled_story = self.library.get_story_by_topic(stack_tail['topic'], stack=stack[:-1])
                if stack_tail['step'] < len(compiled_story.story_line):
                    # if we haven't reach last step in list of story so we can parse result
                    break

                stack.pop()

            validator = matchers.deserialize(stack_tail['data'])
            new_ctx_story = await self.get_deeper_story(compiled_story.story_line[stack_tail['step']],
                                                        validator.validate(message))

            if new_ctx_story:
                compiled_story = new_ctx_story
                self.build_new_scope(stack, new_ctx_story)

            waiting_for = await self.process_story(
                message=message,
                compiled_story=compiled_story,
            )

            self.may_drop_scope(compiled_story, stack, waiting_for)

        return waiting_for

    async def get_deeper_story(self, story_part, validation_result):
        """

        :param story_part:
        :param validation_result:
        :return:
        """
        if hasattr(story_part, 'get_child_by_validation_result'):
            return story_part.get_child_by_validation_result(validation_result)
        else:
            return None

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

            logger.debug('self.tracker')
            logger.debug(self.tracker)
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
                    new_ctx_story = await self.get_deeper_story(story_part, waiting_for.value)
                if new_ctx_story:
                    self.build_new_scope(message['session']['stack'], new_ctx_story)
                    waiting_for = await self.process_story(
                        message=message,
                        compiled_story=new_ctx_story,
                    )
                    self.may_drop_scope(new_ctx_story, message['session']['stack'], waiting_for)

                    # we have more stories in a stack and we've already reached the end of last story
                    # if len(session['stack']) > 1 and \
                    #                 session['stack'][-1]['step'] == len(new_ctx_story.story_line) and \
                    #         not isinstance(waiting_for, callable.EndOfStory):
                    #     session['stack'].pop()
                    # should wait for new message income
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
        else:
            logger.debug('[ ] do not drop because')
            if stack[-1]['step'] < len(compiled_story.story_line) - 1:
                logger.debug('> {} (step) >= {} (story_line) - 1'.format(stack[-1]['step'], len(compiled_story.story_line)))
            if waiting_for:
                logger.debug('> waiting_for = {}'.format(waiting_for))
