import logging
from .. import matchers

logger = logging.getLogger(__name__)


class StoryProcessor:
    def __init__(self, parser_instance, library):
        self.parser_instance = parser_instance
        self.library = library

    def match_message(self, message):
        session = message['session']
        if len(session.stack) == 0:
            session.stack = [None]
        else:
            wait_for_message = session.stack[-1]
            if wait_for_message:
                validator = matchers.deserialize(wait_for_message['data'])
                if validator.validate(message):
                    session.stack[-1] = None
                    step = wait_for_message['step']
                    compiled_story = self.library.get_story_by_topic(wait_for_message['topic'])
                    return self.process_story(
                        idx=step,
                        message=message,
                        compiled_story=compiled_story,
                        session=session,
                    )

        compiled_story = self.library.get_right_story(message)
        if not compiled_story:
            return
        return self.process_story(
            idx=0,
            message=message,
            compiled_story=compiled_story,
            session=session,
        )

    def process_story(self, session, message, compiled_story, idx=0, story_args=[], story_kwargs={}):
        logger.debug('process_story {}'.format(session))
        logger.debug('message {}'.format(message))
        logger.debug('story {}'.format(compiled_story))
        logger.debug('idx {}'.format(idx))

        story_line = compiled_story.story_line

        current_stack_level = len(session.stack) - 1

        while idx < len(story_line):
            one_part = story_line[idx]
            idx += 1
            logger.info('going to call: {}'.format(one_part.__name__))
            if message:
                # process common story part
                waiting_for = one_part(message)
            else:
                # process startpoint of callable story
                waiting_for = one_part(*story_args, **story_kwargs)

            if waiting_for:
                # should wait result of async operation
                # (for example answer from user)
                validator = matchers.get_validator(waiting_for)

                session.stack[current_stack_level] = {
                    'type': validator.type,
                    'data': matchers.serialize(validator),
                    'step': idx,
                    'topic': compiled_story.topic,
                }
                return

        # current story line is over
        if len(session.stack) > 1:
            # but it seems that we have hierarchy of callable
            # stories so we should drop current stack element
            # because it is over and return to the previous story
            session.stack.pop()
            if message:
                if 'return' not in message:
                    message['return'] = True
                self.match_message(message)
