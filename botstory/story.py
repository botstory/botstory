import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from . import matchers
from .middlewares.any import any
from .middlewares.text import text
from .utils import is_string


class Core:
    def __init__(self):
        self.stories = []
        self.callable = []

    def clear(self):
        self.stories = []
        self.callable = []

    def add_story(self, one_story):
        self.stories.append(one_story)

    def add_callable(self, one_callable):
        self.callable.append(one_callable)

    def get_callable_by_topic(self, topic):
        return [s for s in self.callable if s['topic'] == topic][0]

    def valid_story(self, message):
        matched_stories = [task for task in self.stories if task['validator'].validate(message)]
        return matched_stories[0] if len(matched_stories) > 0 else None

    def get_story_by_topic(self, topic):
        return [s for s in [*self.callable, *self.stories] if s['topic'] == topic][0]


core = Core()


def get_validator(receive):
    if isinstance(receive, list):
        return any.AnyOf([get_validator(r) for r in receive])
    elif is_string(receive):
        return text.Match(receive)
    else:
        return receive


def on(receive):
    def fn(one_story):
        compiled_story = parser.compile(
            one_story,
        )
        compiled_story['validator'] = get_validator(receive)
        core.add_story(compiled_story)

        return one_story

    return fn


def part():
    def fn(part_of_story):
        parser.part(part_of_story)
        return part_of_story

    return fn


# parse callable
# TODO: should refactor to separate py-file


class Parser:
    def __init__(self):
        self.node = None
        self.middlewares = []

    def compile(self, one_story, middlewares=[]):
        topic = one_story.__name__
        self.middlewares = middlewares
        self.node = ASTNode(topic=topic)
        one_story()

        parts = self.node
        self.node = None

        return {
            'topic': topic,
            'parts': parts,
        }

    def part(self, story_part):
        for m in self.middlewares:
            if m.process_part(self, story_part):
                return True

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

    def append(self, story_part):
        part_name = story_part.__name__,
        if part_name in self.story_names:
            logger.warning('Already have story with name {}. Please use uniq name'.format(part_name))

        self.story_names.add(part_name)
        self.story_line.append(story_part)

    def startpoint(self, *args, **kwargs):
        if 'session' not in kwargs:
            raise AttributeError('Should pass session as well')

        session = kwargs.pop('session')

        # we are going deeper so prepare one more item in stack
        session.stack.append(None)
        process_story(session,
                      # we don't have message yet
                      message=None,
                      story=self.story,
                      idx=0,
                      story_args=args,
                      story_kwargs=kwargs)

        return WaitForCallableReturn()

    @property
    def story(self):
        return core.get_callable_by_topic(self.topic)


parser = Parser()


def callable():
    def fn(callable_story):
        compiled_story = parser.compile(
            callable_story,
        )
        core.add_callable(compiled_story)
        return compiled_story['parts'].startpoint

    return fn


def begin():
    def fn(story_part):
        parser.part(story_part)

    return fn


@matchers.matcher()
class WaitForCallableReturn:
    type = 'WaitForCallableReturn'

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
    else:
        wait_for_message = session.stack[-1]
        if wait_for_message:
            validator = matchers.deserialize(wait_for_message['data'])
            if validator.validate(message):
                session.stack[-1] = None
                step = wait_for_message['step']
                story = core.get_story_by_topic(wait_for_message['topic'])
                return process_story(
                    idx=step,
                    message=message,
                    story=story,
                    session=session,
                )

    story = core.valid_story(message)
    if not story:
        return
    return process_story(
        idx=0,
        message=message,
        story=story,
        session=session,
    )


def process_story(session, message, story, idx=0, story_args=[], story_kwargs={}):
    logger.debug('process_story {}'.format(session))
    logger.debug('message {}'.format(message))
    logger.debug('story {}'.format(story))
    logger.debug('idx {}'.format(idx))

    story_line = story['parts'].story_line

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
        if message:
            if 'return' not in message:
                message['return'] = True
            match_message(message)
