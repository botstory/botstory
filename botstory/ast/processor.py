import logging
import inspect

from botstory.ast import stack_utils
from . import parser, callable, forking
from .. import di, matchers
from ..integrations import mocktracker

logger = logging.getLogger(__name__)


@di.desc(reg=False)
class StoryProcessor:
    def __init__(self, parser_instance, library, middlewares=[]):
        self.library = library
        self.middlewares = middlewares
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
        logger.debug('self.tracker')
        logger.debug(self.tracker)
        self.tracker.new_message(
            user=message and message['user'],
            data=message['data'],
        )

        stack = message['session']['stack']

        waiting_for = None

        while not waiting_for or isinstance(waiting_for, callable.EndOfStory):
            compiled_story = None
            validation_result = None

            if len(stack) == 0:
                compiled_story = self.library.get_global_story(message)
                logger.debug('get_global_story {}'.format(compiled_story))
                if not compiled_story:
                    # there is no stories for such message
                    return None
                stack.append(stack_utils.build_empty_stack_item(compiled_story.topic))
            else:
                stack_tail = None
                logger.debug('  check stack')
                logger.debug('  session = {}'.format(message['session']))

                # looking for first valid matcher
                while True:
                    if len(stack) == 0:
                        # we have reach the bottom of stack
                        logger.debug('  we have reach the bottom of stack '
                                     'so no once has receive this message')
                        return None
                    stack_tail = stack[-1]
                    logger.debug('stack_tail {}'.format(stack_tail))
                    if not stack_tail['data']:
                        # TODO: we shouldn't get such case
                        # because it shows that we have stack that can't catch incoming message
                        # (?) maybe possible case when it is in a middle of hierarchy
                        # and comes because the top one didn't match message

                        # one case - dangling of last part of story
                        # we don't clear stack after returning from story
                        break
                    validator = matchers.deserialize(stack_tail['data'])
                    logger.debug('validator {}'.format(validator))

                    if getattr(validator, 'new_scope', False):
                        # TODO:
                        # we are start new story line here
                        # so we don't need to check whether we still have tail of story
                        break

                    logger.debug("stack_tail['topic'] {}".format(stack_tail['topic']))
                    logger.debug("stack {}".format(stack))
                    logger.debug("self.library.get_story_by_topic(stack_tail['topic'], stack=stack)")
                    logger.debug(self.library.get_story_by_topic(stack_tail['topic'], stack=stack))
                    if stack_tail['step'] < len(
                            self.library.get_story_by_topic(stack_tail['topic'], stack=stack[:-1]).story_line
                    ):
                        # if we haven't reach last step in list of story so we can parse result
                        break

                    stack.pop()

                logger.debug('    after check session.stack = {}'.format(stack))
                logger.debug('      stack_tail = {}'.format(stack_tail))
                if stack_tail and stack_tail['data']:
                    logger.debug('  got it!')
                    validator = matchers.deserialize(stack_tail['data'])
                    validation_result = validator.validate(message)
                    logger.debug('      validation_result {}'.format(validation_result))
                    if not not validation_result:
                        # it seems we find stack item that matches our message
                        compiled_story = self.library.get_story_by_topic(stack_tail['topic'], stack=stack[:-1])

                received_data = await self.process_next_part_of_story({
                    'step': stack[-1]['step'],
                    'story': compiled_story,
                    'stack': stack,
                }, validation_result)
                compiled_story = received_data['story']

            waiting_for = await self.process_story(
                message=message,
                compiled_story=compiled_story,
            )

            if len(stack) == 0:
                break

        return waiting_for

    async def process_next_part_of_story(self, received_data, validation_result):
        logger.debug('')
        logger.debug('process_next_part_of_story')
        logger.debug('')

        received_data['going-deeper'] = False

        # map-reduce process
        for m in self.middlewares:
            if hasattr(m, 'process'):
                received_data = m.process(received_data, validation_result)

        return received_data

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
        idx = current_story['step']
        waiting_for = None
        story_line = compiled_story.story_line

        logger.debug('current_story {} ({})'.format(current_story, len(story_line)))

        # integrate over parts of story
        while idx < len(story_line) and not waiting_for:
            logger.debug('')
            logger.debug('  next iteration of {}'.format(current_story['topic']))
            logger.debug('      idx = {} ({})'.format(idx, len(story_line)))
            logger.debug('      session {}'.format(session['stack']))

            story_part = story_line[idx]

            logger.debug('self.tracker')
            logger.debug(self.tracker)
            self.tracker.story(
                user=message and message['user'],
                story_name=current_story['topic'],
                story_part_name=story_part.__name__,
            )

            idx += 1
            current_story['step'] = idx

            # TODO: just should skip story part
            # but it should be done in process_next_part_of_story
            if isinstance(story_part, parser.StoryPartFork):
                # looking for story part after StoryPartFork
                # it possible because previous story part result
                # didn't match any StoryPartFork cases or
                # match and already played it
                logger.debug('  skip StoryPartFork')
                continue

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

            if waiting_for:
                if isinstance(waiting_for, forking.SwitchOnValue):
                    # SwitchOnValue is so special because it is the only result
                    # that doesn't async.
                    logger.debug('try to go deeper')
                    received_data = await self.process_next_part_of_story({
                        'step': idx,
                        'story': compiled_story,
                        'stack': message['session']['stack'],
                    }, waiting_for.value)

                    if received_data['going-deeper']:
                        logger.debug('[>] going deeper')
                        processed_story = received_data['story']
                        waiting_for = await self.process_story(
                            message=message,
                            compiled_story=received_data['story'],
                        )

                        logger.debug('[<] return')

                        # we have more stories in a stack and we've already reached the end of last story
                        if len(session['stack']) > 1 and \
                                        session['stack'][-1]['step'] == len(processed_story.story_line) and \
                                not isinstance(waiting_for, callable.EndOfStory):
                            session['stack'].pop()
                    else:
                        # we just skip this waiting for result
                        # and aren't going deeper to switch
                        waiting_for = None
                elif isinstance(waiting_for, callable.EndOfStory):
                    if message:
                        message['data'] = {**message['data'], **waiting_for.data}
                else:
                    current_story['data'] = matchers.serialize(
                        matchers.get_validator(waiting_for)
                    )

        if idx == len(story_line):
            logger.debug('[!] played story line through')
            session['stack'].pop()

        return waiting_for
