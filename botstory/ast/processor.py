import asyncio
import logging
import inspect

from .. import matchers
from . import parser, callable, forking

logger = logging.getLogger(__name__)


class StoryProcessor:
    def __init__(self, parser_instance, library, middlewares=[]):
        self.interfaces = []
        self.library = library
        self.middlewares = middlewares
        self.parser_instance = parser_instance
        self.storage = None

    def add_interface(self, interface):
        if self.storage:
            interface.add_storage(self.storage)
        self.interfaces.append(interface)
        interface.processor = self

    def add_storage(self, storage):
        self.storage = storage
        for interface in self.interfaces:
            interface.add_storage(storage)

    async def match_message(self, message):
        logger.debug('')
        logger.debug('> match_message <')
        logger.debug('')
        logger.debug('  {} '.format(message))
        session = message['session']
        if len(session['stack']) > 0:
            logger.debug('  check stack')
            logger.debug('    session.stack = {}'.format(session['stack']))
            stack_tail = None
            while True:
                if len(session['stack']) == 0:
                    # we have reach the bottom of stack
                    # if stack_tail and stack_tail['data']:
                    #     validator = matchers.deserialize(stack_tail['data'])
                    #     if validator.validate(message):
                    #         # it seems that last callee in a stack should receive
                    #         # this message but it doesn't have more story parts
                    #         # so we just skip this message
                    #         return
                    # stack_tail = None
                    logger.debug('  we have reach the bottom of stack '
                                 'so no once has receive this message')
                    return None
                stack_tail = session['stack'].pop()
                if not stack_tail['data']:
                    break
                validator = matchers.deserialize(stack_tail['data'])
                if hasattr(validator, 'immediately') and validator.immediately:
                    return
                if stack_tail['step'] < len(
                        self.library.get_story_by_topic(stack_tail['topic'], stack=session['stack']).story_line
                ):
                    # if we haven't reach last step in list of story so we can parse result
                    break

            logger.debug('    after check session.stack = {}'.format(session['stack']))
            if stack_tail:
                logger.debug('      topic {}'.format(stack_tail['topic']))
                logger.debug('      step {}'.format(stack_tail['step']))
            logger.debug('      stack_tail = {}'.format(stack_tail))
            if stack_tail and stack_tail['data']:
                logger.debug('  got it!')
                validator = matchers.deserialize(stack_tail['data'])
                validation_result = validator.validate(message)
                logger.debug('      validation_result {}'.format(validation_result))
                if not not validation_result:
                    return await self.process_next_part_of_story({
                        'step': stack_tail['step'],
                        'story': self.library.get_story_by_topic(stack_tail['topic'], stack=session['stack']),
                        'stack_tail': [stack_tail],
                    },
                        validation_result, session, message,
                        bubble_up=True)

        if len(session['stack']) == 0:
            session['stack'] = [build_empty_stack_item()]

        compiled_story = self.library.get_right_story(message)
        if not compiled_story:
            return
        return await self.process_story(
            idx=0,
            message=message,
            compiled_story=compiled_story,
            session=session,
            bubble_up=True,
        )

    async def process_story(self, session, message, compiled_story, idx=0, story_args=[], story_kwargs={},
                            bubble_up=True):
        logger.debug('')
        logger.debug('process_story')
        logger.debug('')

        logger.debug('  bubble_up {}'.format(bubble_up))
        logger.debug('! topic {}'.format(compiled_story.topic))
        logger.debug('! step {}'.format(idx))
        logger.debug('  story {}'.format(compiled_story))
        logger.debug('  message {}'.format(message))
        logger.debug('  session.stack {} ({})'.format(session['stack'], len(session['stack'])))
        logger.debug(
            '  previous_topics: {}'.format(session['stack'][-2]['topic'] if len(session['stack']) > 1 else None))

        story_line = compiled_story.story_line

        current_stack_level = len(session['stack']) - 1
        session['stack'][-1]['topic'] = compiled_story.topic

        waiting_for = None

        while idx < len(story_line):
            logger.debug('')
            logger.debug('  next iteration of {}'.format(compiled_story.topic))
            logger.debug('      idx = {} ({})'.format(idx, len(story_line)))
            logger.debug('      session {}'.format(session['stack']))

            story_part = story_line[idx]

            logger.debug('  going to call: {}'.format(story_part.__name__))

            # TODO: just should skip story part
            # but it should be done in process_next_part_of_story
            if not isinstance(story_part, parser.StoryPartFork):
                if message:
                    # process common story part
                    waiting_for = story_part(message)
                else:
                    # process startpoint of callable story
                    waiting_for = story_part(*story_args, **story_kwargs)

                if inspect.iscoroutinefunction(story_part):
                    waiting_for = await waiting_for

                logger.debug('  got result {}'.format(waiting_for))

            idx += 1
            if len(session['stack']) > current_stack_level:
                session['stack'][current_stack_level]['step'] = idx

            # TODO: should be refactor and put somewhere
            if waiting_for:
                # story part return value so we should somehow react on it
                if isinstance(waiting_for, forking.SwitchOnValue):
                    # SwitchOnValue is so special because it is the only result
                    # that doesn't async.
                    waiting_for = await forking.process_switch_on_value(compiled_story,
                                                                        idx, message, self, session, waiting_for)

                    if waiting_for:
                        logger.debug('  bubble up')
                        if bubble_up and isinstance(waiting_for, callable.EndOfStory):
                            break
                        else:
                            # if processed story part is waiting for result
                            # neither this story should continue working
                            return waiting_for

                elif isinstance(waiting_for, callable.EndOfStory):
                    if bubble_up:
                        break
                    return callable.process_end_of_story(message, waiting_for)
                else:
                    return process_async_operation(compiled_story, current_stack_level,
                                                   idx, self, session, waiting_for)

        # current story line is over
        if len(session['stack']) > 1:
            logger.debug('  we can bobble by stack')
            # but it seems that we have hierarchy of callable
            # stories so we should drop current stack element
            # because it is over and return to the previous story

            logger.debug('  action: reduce stack -1')
            session['stack'].pop()
            logger.debug('  session.stack = {}'.format(session['stack']))

            if message:
                if bubble_up:
                    waiting_for = await self.match_message(message)
                else:
                    logger.debug('  we reject bubbling in this call')

        return waiting_for

    async def process_next_part_of_story(self, received_data, validation_result, session, message, bubble_up=True):
        logger.debug('')
        logger.debug('process_next_part_of_story')
        logger.debug('')
        logger.debug('  topic {}'.format(received_data['story'].topic))
        logger.debug('  step {} ({})'.format(received_data['step'], len(received_data['story'].story_line)))

        for m in self.middlewares:
            if hasattr(m, 'process'):
                received_data = m.process(received_data, validation_result)

        logger.debug('  len(session.stack) = {}'.format(len(session['stack'])))
        logger.debug('  session.stack = {}'.format(session['stack']))
        logger.debug('  action: extend stack by +{}'.format(len(received_data['stack_tail'])))

        session['stack'].extend(received_data['stack_tail'])
        session['stack'][-1] = build_empty_stack_item()

        logger.debug('  session.stack = {}'.format(session['stack']))
        logger.debug('! after topic {}'.format(received_data['story'].topic))
        logger.debug('! after step {}'.format(received_data['step']))

        # we shouldn't bubble up because we inside other story
        # that under control
        return await self.process_story(
            idx=received_data['step'],
            message=message,
            compiled_story=received_data['story'],
            session=session,
            bubble_up=bubble_up,
        )


def process_async_operation(compiled_story, current_stack_level, idx, processor, session, waiting_for):
    # should wait result of async operation
    # (for example answer from user)
    for m in processor.middlewares:
        if hasattr(m, 'process_validator'):
            waiting_for = m.process_validator(processor, waiting_for, compiled_story)

    validator = matchers.get_validator(waiting_for)

    logger.debug('  before serialize validator')

    session['stack'][current_stack_level] = {
        'type': validator.type,
        'data': matchers.serialize(validator),
        'step': idx,
        'topic': compiled_story.topic,
    }
    return waiting_for


def build_empty_stack_item():
    return {
        'data': None,
        'step': 0,
        'topic': None,
    }
