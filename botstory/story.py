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
        session.current_topic = self.topic

        wait_for = self.endpoint_story(*args, **kwargs)

        if wait_for:
            session.wait_for_message = {
                'type': wait_for.type,
                'data': matchers.serialize(get_validator(wait_for)),
                'step': 1,
            }


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


def match_message(message):
    session = message['session']
    print('match_message')
    print('session.wait_for_message', session.wait_for_message)
    if session.wait_for_message:
        validator = matchers.deserialize(session.wait_for_message['data'])
        if validator.validate(message):
            step = session.wait_for_message['step']
            session.wait_for_message = None
            story = [s for s in [*core['callable'], *core['stories']] if s['topic'] == session.current_topic][0]
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
    session.current_topic = story['topic']
    return process_story(
        idx=0,
        message=message,
        story=story,
        session=session,
    )


def process_story(session, message, story, idx=0):
    print('process_story', session, message, story, idx)
    parts = story['parts']
    if hasattr(parts, 'story_line'):
        parts = parts.story_line

    while idx < len(parts):
        one_part = parts[idx]
        idx += 1
        validator = one_part(message)
        if validator:
            # TODO: should wait result of async operation
            # (for example answer from user)
            validator = get_validator(validator)
            session.wait_for_message = {
                'type': validator.type,
                'data': matchers.serialize(validator),
                'step': idx,
            }
            return
