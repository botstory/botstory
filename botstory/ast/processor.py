import logging
import inspect

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
        because match_message is recursive we split function to
        public match_message and private _match_message

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

        waiting_for = await self._match_message(message)

        session = message['session']
        while (not waiting_for or isinstance(waiting_for, callable.EndOfStory)) \
                and len(session['stack']) > 1:
            # if len(session['stack']) > 1:
            logger.debug('  we can bobble by stack')
            logger.debug('  session.stack = {}'.format(session['stack']))
            # but it seems that we have hierarchy of callable
            # stories so we should drop current stack element
            # because it is over and return to the previous story

            session['stack'].pop()

            if message:
                waiting_for = await self._match_message(message)

        return waiting_for

    async def _match_message(self, message):
        session = message['session']
        logger.debug('_match_message')
        if len(session['stack']) > 0:
            logger.debug('  check stack')
            logger.debug('    session.stack = {}'.format(session['stack']))
            stack_tail = None

            # looking for first valid matcher
            while True:
                if len(session['stack']) == 0:
                    # we have reach the bottom of stack
                    logger.debug('  we have reach the bottom of stack '
                                 'so no once has receive this message')
                    return None
                stack_tail = session['stack'].pop()
                logger.debug('stack_tail {}'.format(stack_tail))
                if not stack_tail['data']:
                    break
                validator = matchers.deserialize(stack_tail['data'])
                logger.debug('validator {}'.format(validator))
                if hasattr(validator, 'immediately') and validator.immediately:
                    logger.debug('return from  _match_message')
                    return True

                if getattr(validator, 'new_scope', False):
                    # we are start new story line here
                    # so we don't need to check whether we still have tail of story
                    break

                logger.debug("stack_tail['topic'] {}".format(stack_tail['topic']))
                logger.debug("session['stack'] {}".format(session['stack']))
                logger.debug("self.library.get_story_by_topic(stack_tail['topic'], stack=session['stack'])")
                logger.debug(self.library.get_story_by_topic(stack_tail['topic'], stack=session['stack']))
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
                    _, waiting_for = await self.process_next_part_of_story({
                        'step': stack_tail['step'],
                        'story': self.library.get_story_by_topic(stack_tail['topic'], stack=session['stack']),
                        'stack_tail': [stack_tail],
                    },
                        validation_result, session, message)
                    return waiting_for

        if len(session['stack']) == 0:
            session['stack'] = [build_empty_stack_item()]

        compiled_story = self.library.get_right_story(message)
        if not compiled_story:
            return True

        return await self.process_story(
            idx=0,
            message=message,
            compiled_story=compiled_story,
            session=session,
        )

    async def process_story(self, session, message, compiled_story,
                            idx=0, story_args=[], story_kwargs={},
                            ):
        logger.debug('')
        logger.debug('process_story')
        logger.debug('')

        logger.debug('! topic {}'.format(compiled_story.topic))
        logger.debug('! step {}'.format(idx))
        logger.debug('  story {}'.format(compiled_story))
        logger.debug('  message {}'.format(message))
        logger.debug('  session.stack {} ({})'.format(session['stack'], len(session['stack'])))
        logger.debug(
            '  previous_topics: {}'.format(session['stack'][-2]['topic'] if len(session['stack']) > 1 else None))

        story_line = compiled_story.story_line

        current_story = session['stack'][-1]
        session['stack'][-1]['topic'] = compiled_story.topic

        waiting_for = None

        # integrate over parts of story
        while idx < len(story_line):
            logger.debug('')
            logger.debug('  next iteration of {}'.format(compiled_story.topic))
            logger.debug('      idx = {} ({})'.format(idx, len(story_line)))
            logger.debug('      session {}'.format(session['stack']))

            story_part = story_line[idx]

            logger.debug('  going to call: {}'.format(story_part.__name__))

            logger.debug('self.tracker')
            logger.debug(self.tracker)
            self.tracker.story(
                user=message and message['user'],
                story_name=compiled_story.topic,
                story_part_name=story_part.__name__,
            )

            idx += 1
            session['stack'][-1]['step'] = idx

            # TODO: just should skip story part
            # but it should be done in process_next_part_of_story
            if isinstance(story_part, parser.StoryPartFork):
                # looking for story part after StoryPartFork
                # it possible because previous story part result
                # didn't match any StoryPartFork cases or
                # match and already played it
                continue

            if message:
                # process common story part
                waiting_for = story_part(message)
            else:
                # process startpoint of callable story
                waiting_for = story_part(*story_args, **story_kwargs)

            if inspect.iscoroutinefunction(story_part):
                waiting_for = await waiting_for

            logger.debug('  got result {}'.format(waiting_for))

            # TODO: should be refactor and put somewhere
            if waiting_for:
                # story part return value so we should somehow react on it
                if isinstance(waiting_for, forking.SwitchOnValue):
                    # SwitchOnValue is so special because it is the only result
                    # that doesn't async.

                    processed_story, waiting_for = await self.process_next_part_of_story({
                        'step': idx,
                        'story': compiled_story,
                        'stack_tail': [session['stack'].pop()],
                    },
                        waiting_for.value, session, message)

                    # we have more stories in a stack and we've already reached the end of last story
                    if len(session['stack']) > 1 and \
                                    session['stack'][-1]['step'] == len(processed_story.story_line) and \
                            not isinstance(waiting_for, callable.EndOfStory):
                        logger.debug('popup')
                        session['stack'].pop()

                if waiting_for:
                    if isinstance(waiting_for, callable.EndOfStory):
                        if message:
                            message['data'] = {**message['data'], **waiting_for.data}
                    else:
                        current_story['data'] = matchers.serialize(
                            matchers.get_validator(waiting_for)
                        )
                    logger.debug('return from process_story')
                    return waiting_for

        return waiting_for

    async def process_next_part_of_story(self, received_data, validation_result, session, message):
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

        session['stack'].extend(
            received_data['stack_tail'][:-1] + [build_empty_stack_item()]
        )

        logger.debug('  session.stack = {}'.format(session['stack']))
        logger.debug('! after topic {}'.format(received_data['story'].topic))
        logger.debug('! after step {}'.format(received_data['step']))

        # we shouldn't bubble up because we inside other story
        # that under control
        waiting_for = await self.process_story(
            idx=received_data['step'],
            message=message,
            compiled_story=received_data['story'],
            session=session,
        )

        return received_data['story'], waiting_for


def build_empty_stack_item():
    return {
        'data': None,
        'step': 0,
        'topic': None,
    }
