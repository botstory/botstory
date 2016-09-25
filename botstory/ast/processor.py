import logging

logger = logging.getLogger(__name__)

from .. import matchers
from . import parser, callable


class StoryProcessor:
    def __init__(self, parser_instance, library, middlewares=[]):
        self.parser_instance = parser_instance
        self.library = library
        self.middlewares = middlewares

    def match_message(self, message):
        logger.debug('')
        logger.debug('match_message {} '.format(message))
        logger.debug('')
        session = message['session']
        if len(session.stack) > 0:
            logger.debug('  check stack')
            logger.debug('    session.stack = {}'.format(session.stack))
            stack_tail = None
            while True:
                if len(session.stack) == 0:
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
                stack_tail = session.stack.pop()
                if not stack_tail['data']:
                    break
                validator = matchers.deserialize(stack_tail['data'])
                if hasattr(validator, 'immediately') and validator.immediately:
                    return
                if stack_tail['step'] < len(
                        self.library.get_story_by_topic(stack_tail['topic'], stack=session.stack).story_line
                ):
                    # if we haven't reach last step in list of story so we can parse result
                    break
                if 'return' not in message:
                    message['return'] = True

            logger.debug('    after check session.stack = {}'.format(session.stack))
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
                    # wait_for_message['data'] = None

                    # TODO: should remove!
                    # if wait_for_message['topic'] == 'one_story_1' and wait_for_message['step'] == 2:
                    #     logger.debug('>>> assert False')
                    # assert False
                    # logger.debug('  action: reduce stack by -1')

                    # stack_tail = None
                    # while not stack_tail
                    #     and len(session.stack) > 0:
                    #     stack_tail = session.stack.pop()

                    # stack_tail = session.stack.pop()

                    # logger.debug('  session.stack = {}'.format(session.stack))
                    return self.process_next_part_of_story({
                        'step': stack_tail['step'],
                        'story': self.library.get_story_by_topic(stack_tail['topic'], stack=session.stack),
                        'stack_tail': [stack_tail],
                    },
                        validation_result, session, message,
                        bubble_up=True)
                    # else:
                    #     assert False

        if len(session.stack) == 0:
            session.stack = [build_empty_stack_item()]

        compiled_story = self.library.get_right_story(message)
        if not compiled_story:
            return
        return self.process_story(
            idx=0,
            message=message,
            compiled_story=compiled_story,
            session=session,
            bubble_up=True,
        )

    def process_story(self, session, message, compiled_story, idx=0, story_args=[], story_kwargs={}, bubble_up=True):
        logger.debug('')
        logger.debug('process_story')
        logger.debug('')

        # TODO: new fix
        # if len(session.stack) == 0:
        #     return False

        logger.debug('  bubble_up {}'.format(bubble_up))
        logger.debug('! topic {}'.format(compiled_story.topic))
        logger.debug('! step {}'.format(idx))
        logger.debug('  story {}'.format(compiled_story))
        logger.debug('  message {}'.format(message))
        logger.debug('  session.stack {} ({})'.format(session.stack, len(session.stack)))
        logger.debug('  previous_topics: {}'.format(session.stack[-2]['topic'] if len(session.stack) > 1 else None))

        story_line = compiled_story.story_line

        current_stack_level = len(session.stack) - 1
        session.stack[-1]['topic'] = compiled_story.topic
        # session.stack[-1]['topic'] = compiled_story.topic

        waiting_for = None

        while idx < len(story_line):
            logger.debug('')
            logger.debug('  next iteration of {}'.format(compiled_story.topic))
            logger.debug('      idx = {} ({})'.format(idx, len(story_line)))
            logger.debug('      session {}'.format(session.stack))

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

                logger.debug('  got result {}'.format(waiting_for))
                if waiting_for:
                    # story part return value so we should somehow react on it
                    if hasattr(waiting_for, 'immediately'):
                        # ... without waiting for user feedback
                        logger.debug('  process immediately')

                        # it seems that next item can use passed values
                        idx += 1
                        session.stack[current_stack_level]['step'] = idx

                        waiting_for = self.process_next_part_of_story({
                            'step': idx,
                            'story': compiled_story,
                            'stack_tail': [session.stack.pop()],
                        },
                            waiting_for.value, session, message,
                            bubble_up=False)

                        # TODO:
                        # should check whether we test case
                        # when we got request to wait for user feedback
                        # inside of fork
                        # and now should wait for result
                        # then just prevent processing until result

                        # it should be something like this
                        # if waiting_for and not hasattr(waiting_for, 'immediately'):
                        #     return

                        logger.debug('  after process_next_part_of_story')
                        logger.debug('      waiting_for = {}'.format(waiting_for))
                        logger.debug('      session.stack = {}'.format(session.stack))
                        logger.debug('      bubble_up = {}'.format(bubble_up))
                        if waiting_for:
                            logger.debug('  bubble up')
                            if bubble_up and isinstance(waiting_for, callable.EndOfStory):
                                break
                            else:
                                # if processed story part is waiting for result
                                # neither this story should continue working
                                return waiting_for
                    elif isinstance(waiting_for, callable.EndOfStory):
                        logger.debug('  got EndOfStory!')
                        # TODO: should be refactor and put somewhere
                        # TODO: once we put all data to message['data']
                        # message['data'] = {**message['data'], **waiting_for.res}
                        # but now we should have temporal solution:
                        for key, value in waiting_for.res.items():
                            message[key] = value
                        return waiting_for
                    else:
                        # should wait result of async operation
                        # (for example answer from user)
                        for m in self.middlewares:
                            if hasattr(m, 'process_validator'):
                                waiting_for = m.process_validator(self, waiting_for, compiled_story)

                        validator = matchers.get_validator(waiting_for)

                        logger.debug('  before serialize validator')

                        session.stack[current_stack_level] = {
                            'type': validator.type,
                            'data': matchers.serialize(validator),
                            'step': idx + 1,
                            'topic': compiled_story.topic,
                        }
                        return waiting_for

            idx += 1
            if len(session.stack) > current_stack_level:
                session.stack[current_stack_level]['step'] = idx

        # current story line is over
        if len(session.stack) > 1:
            logger.debug('  we can bobble by stack')
            # but it seems that we have hierarchy of callable
            # stories so we should drop current stack element
            # because it is over and return to the previous story

            logger.debug('  action: reduce stack -1')
            session.stack.pop()
            logger.debug('  session.stack = {}'.format(session.stack))

            if message:
                if 'return' not in message:
                    message['return'] = True
                # TODO: should remove!
                if compiled_story.topic == 'other_sides':
                    logger.debug('  session.stack {}'.format(session.stack))
                    logger.debug('  message.session {}'.format(message['session'].stack))
                    logger.debug('  message {}'.format(message))
                    # assert False
                if bubble_up:
                    waiting_for = self.match_message(message)
                else:
                    logger.debug('  we reject bubbling in this call')

        return waiting_for

    def process_next_part_of_story(self, received_data, validation_result, session, message, bubble_up=True):
        logger.debug('')
        logger.debug('process_next_part_of_story')
        logger.debug('')
        logger.debug('  topic {}'.format(received_data['story'].topic))
        logger.debug('  step {} ({})'.format(received_data['step'], len(received_data['story'].story_line)))

        # TODO: new fix
        # if received_data['step'] >= len(received_data['story'].story_line):
        #     session.stack.extend(received_data['stack_tail'])
        #     return False

        # TODO: should remove
        # should_stop_after = False
        # if received_data['story'].topic == 'one_story_1' and received_data['step'] == 1:
        #     should_stop_after = True

        for m in self.middlewares:
            received_data = m.process(received_data, validation_result)

        logger.debug('  len(session.stack) = {}'.format(len(session.stack)))
        logger.debug('  session.stack = {}'.format(session.stack))
        logger.debug('  action: extend stack by +{}'.format(len(received_data['stack_tail'])))

        session.stack.extend(received_data['stack_tail'])
        session.stack[-1] = build_empty_stack_item()

        logger.debug('  session.stack = {}'.format(session.stack))
        logger.debug('! after topic {}'.format(received_data['story'].topic))
        logger.debug('! after step {}'.format(received_data['step']))

        # TODO: should remove!
        # if should_stop_after:
        #     assert False

        # we shouldn't bubble up because we inside other story
        # that under control
        return self.process_story(
            idx=received_data['step'],
            message=message,
            compiled_story=received_data['story'],
            session=session,
            bubble_up=bubble_up,
        )

        # return received_data


def build_empty_stack_item():
    return {
        'data': None,
        'step': 0,
        'topic': None,
    }
