import logging

logger = logging.getLogger(__name__)

from .. import matchers


class StoryProcessor:
    def __init__(self, parser_instance, library, middlewares=[]):
        self.parser_instance = parser_instance
        self.library = library
        self.middlewares = middlewares

    def match_message(self, message):
        logger.debug('match_message {} '.format(message))
        session = message['session']
        if len(session.stack) == 0:
            session.stack = [build_empty_stack_item()]
        else:
            wait_for_message = session.stack[-1]
            if wait_for_message['data']:
                validator = matchers.deserialize(wait_for_message['data'])
                validation_result = validator.validate(message)
                if not not validation_result:
                    return self.process_next_part_of_story({
                        'step': wait_for_message['step'],
                        'story': self.library.get_story_by_topic(wait_for_message['topic']),
                        'stack_tail': [session.stack.pop()],
                    }, validation_result, session, message)

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
        logger.debug('  message {}'.format(message))
        logger.debug('  story {}'.format(compiled_story))
        logger.debug('  session.stack {}'.format(session.stack))
        logger.debug('  idx {}'.format(idx))

        story_line = compiled_story.story_line

        current_stack_level = len(session.stack) - 1

        session.stack[-1]['topic'] = compiled_story.topic

        while idx < len(story_line):
            one_part = story_line[idx]
            idx += 1
            session.stack[-1]['step'] = idx
            logger.info('going to call: {}'.format(one_part.__name__))

            if message:
                # process common story part
                waiting_for = one_part(message)
            else:
                # process startpoint of callable story
                waiting_for = one_part(*story_args, **story_kwargs)

            if waiting_for:
                # story part return value so we should somehow react on it
                if hasattr(waiting_for, 'immediately'):
                    # ... without waiting for user feedback
                    self.process_next_part_of_story({
                        'step': idx,
                        'story': compiled_story,
                        'stack_tail': [session.stack.pop()],
                    }, waiting_for.value, session, message)
                else:
                    # ot wait result of async operation
                    # (for example answer from user)
                    for m in self.middlewares:
                        if hasattr(m, 'process_validator'):
                            waiting_for = m.process_validator(self, waiting_for, compiled_story)

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

    def process_next_part_of_story(self, received_data, validation_result, session, message):
        for m in self.middlewares:
            received_data = m.process(received_data, validation_result)

        session.stack.extend(received_data['stack_tail'])
        session.stack[-1] = build_empty_stack_item()
        return self.process_story(
            idx=received_data['step'],
            message=message,
            compiled_story=received_data['story'],
            session=session,
        )


def build_empty_stack_item():
    return {
        'data': None,
        'step': 0,
        'topic': None,
    }
