import logging

logger = logging.getLogger('story')

from . import matchers
from .middlewares.any import any
from .middlewares.text import text
from .utils import is_string

core = {
    'stories': [],
    'callable': [],
}


def clear():
    core['callable'] = []
    core['stories'] = []


def get_validator(receive):
    if isinstance(receive, list):
        return any.AnyOf([get_validator(r) for r in receive])
    elif is_string(receive):
        return text.Match(receive)
    else:
        return receive


def on(receive):
    def fn(one_story):
        validator = get_validator(receive)

        core['stories'].append({
            'validator': validator,
            'topic': one_story.__name__,
            'parts': []
        })

        # to parse inner sub-stories
        one_story()

    return fn


def part():
    def fn(part_of_story):
        if not parser.part(part_of_story):
            last_story = core['stories'][-1]
            last_story['parts'].append(part_of_story)

    return fn


# parse callable
# TODO: should refactor to separate py-file


class Parser:
    def __init__(self):
        self.node = None

    def compile(self, one_story):
        topic = one_story.__name__
        self.node = ASTNode(topic=topic)
        one_story()

        return {
            'topic': topic,
            'parts': self.node,
        }

    def begin(self, story_part):
        if not self.node:
            return False
        self.node.endpoint_story = story_part
        self.node.append(self.node.endpoint)
        return True

    def part(self, story_part):
        if not self.node:
            return False
        self.node.append(story_part)
        return True

    @property
    def topic(self):
        return self.node.topic


class ASTNode:
    def __init__(self, topic):
        self.topic = topic
        self.story_line = []
        self.story_names = set()
        self.endpoint_story = None

    def append(self, story_part):
        part_name = story_part.__name__,
        if part_name in self.story_names:
            logger.warning('Already have story with name {}. Please use uniq name'.format(part_name))

        self.story_names.add(part_name)
        self.story_line.append(story_part)

    @property
    def first_part(self):
        return self.story_line[0]

    def endpoint(self, *args, **kwargs):
        if 'session' not in kwargs:
            raise AttributeError('Should pass session as well')

        session = kwargs.pop('session')

        # TODO : should use process_story()
        wait_for = self.endpoint_story(*args, **kwargs)

        if wait_for:
            session.stack.append({
                'type': wait_for.type,
                'data': matchers.serialize(get_validator(wait_for)),
                'step': 1,
                'topic': self.topic,
            })

        return WaitForCallable()


parser = Parser()


def callable():
    def fn(callable_story):
        compiled_story = parser.compile(callable_story)
        core['callable'].append(compiled_story)
        parser.node = None
        return compiled_story['parts'].first_part

    return fn


def begin():
    def fn(story_part):
        parser.begin(story_part)

    return fn


@matchers.matcher()
class WaitForCallable:
    type = 'CallableReceiver'

    def __init__(self):
        pass

    def validate(self, message):
        return 'return' in message


# match incoming messages
# TODO: should refactor to separate py-file


def match_message(message):
    session = message['session']
    if len(session.stack) == 0:
        session.stack = [None]
        wait_for_message = None
    else:
        wait_for_message = session.stack[-1]
    if wait_for_message:
        validator = matchers.deserialize(wait_for_message['data'])
        if validator.validate(message):
            session.stack[-1] = None
            step = wait_for_message['step']
            story = [s for s in [*core['callable'], *core['stories']] if s['topic'] == wait_for_message['topic']][0]
            return process_story(
                idx=step,
                message=message,
                story=story,
                session=session,
            )

    matched_stories = [task for task in core['stories'] if task['validator'].validate(message)]
    if len(matched_stories) == 0:
        return

    story = matched_stories[0]
    return process_story(
        idx=0,
        message=message,
        story=story,
        session=session,
    )


def process_story(session, message, story, idx=0):
    logger.debug('process_story {}'.format(session))
    logger.debug('message {}'.format(message))
    logger.debug('story {}'.format(story))
    logger.debug('idx {}'.format(idx))

    parts = story['parts']
    if hasattr(parts, 'story_line'):
        parts = parts.story_line

    current_stack_level = len(session.stack) - 1

    while idx < len(parts):
        one_part = parts[idx]
        idx += 1
        logger.info('going to call: {}'.format(one_part.__name__))
        waiting_for = one_part(message)
        if waiting_for:
            # should wait result of async operation
            # (for example answer from user)
            validator = get_validator(waiting_for)

            session.stack[current_stack_level] = {
                'type': validator.type,
                'data': matchers.serialize(validator),
                'step': idx,
                'topic': story['topic'],
            }
            return

    # current story line is over
    if len(session.stack) > 1:
        # but it seems that we have hierarchy of callable
        # stories so we should drop current stack element
        # because it is over and return to the previous story
        session.stack.pop()
        if 'return' not in message:
            message['return'] = True
        match_message(message)
