from botstory import matchers, utils
from botstory.ast import callable, forking, loop
from botstory.ast.story_context import reducers
from botstory.utils import advanced_json_encoder

import logging
import uuid

logger = logging.getLogger(__name__)


class MissedStoryPart(Exception):
    pass


class StoryContext:
    def __init__(self, message, library, matched=False, waiting_for=None, parent_uid=None):
        self.uid = str(uuid.uuid4())
        self.parent_uid = parent_uid
        self.library = library
        # whether message was passed validation and was matched one story
        self.matched = matched
        self.message = message
        self.waiting_for = waiting_for

    def clone(self):
        return StoryContext(library=self.library,
                            matched=self.matched,
                            message=self.message,
                            parent_uid=self.uid,
                            waiting_for=self.waiting_for,
                            )

    def compiled_story(self):
        if self.is_empty_stack():
            return self.library.get_global_story(self.message)
        else:
            return self.library.get_story_by_topic(self.stack_tail()['topic'], stack=self.stack()[:-1])

    def could_scope_out(self):
        """
        could bubble up from current scope

        :return:
        """
        return not self.waiting_for or \
               isinstance(self.waiting_for, callable.EndOfStory) or \
               self.is_breaking_a_loop()

    def current_step(self):
        return self.stack_tail()['step']

    def does_it_match_any_story(self):
        return self.compiled_story() is not None and not self.matched

    def get_child_story(self):
        """
        try child story that match message and get scope of it
        :return:
        """
        story_loop = self.compiled_story()
        if isinstance(story_loop, loop.StoriesLoopNode) and \
                not self.matched:
            validator = story_loop.children_matcher()
            topic = validator.validate(self.message)
            # if topic == None:
            # we inside story loop scope
            # but got message that doesn't match
            # any local stories
            return story_loop.by_topic(topic)

        story_part = self.get_current_story_part()

        if not hasattr(story_part, 'get_child_by_validation_result'):
            return None

        if isinstance(self.waiting_for, forking.SwitchOnValue):
            return story_part.get_child_by_validation_result(self.waiting_for.value)

        stack_tail = self.stack_tail()
        if stack_tail['data'] is not None and not self.matched:
            validator = matchers.deserialize(stack_tail['data'])
            validation_result = validator.validate(self.message)
            return story_part.get_child_by_validation_result(validation_result)

        return None

    def get_current_story_part(self):
        compiled_story = self.compiled_story()
        if not compiled_story:
            return None
        try:
            return compiled_story.story_line[self.current_step()]
        except IndexError:
            return None

    def get_user_data(self):
        return get_user_data(self.message)

    def has_child_story(self):
        return self.get_child_story() is not None

    def is_breaking_a_loop(self):
        return isinstance(self.waiting_for, loop.BreakLoop)

    def is_empty_stack(self):
        return len(self.stack()) == 0

    def is_end_of_story(self):
        compiled_story = self.compiled_story()
        if not compiled_story:
            return True
        return self.current_step() >= len(compiled_story.story_line)

    def is_scope_level(self):
        return isinstance(self.compiled_story(), loop.StoriesLoopNode)

    def is_scope_level_part(self):
        return isinstance(self.get_current_story_part(), loop.StoriesLoopNode)

    def is_tail_of_story(self):
        compiled_story = self.compiled_story()
        if not compiled_story:
            return True
        return self.current_step() >= len(compiled_story.story_line) - 1

    def is_waiting_for_input(self):
        """
        could make one step further
        :return:
        """
        return self.waiting_for and \
               not isinstance(self.waiting_for, forking.SwitchOnValue)

    def stack(self):
        return self.message['session']['stack']

    def stack_tail(self):
        stack = self.stack()
        if len(stack) == 0:
            raise MissedStoryPart()
        return stack[-1]

    def to_json(self):
        return {
            'uid': self.uid,
            'parent_uid': self.parent_uid,
            'matched': self.matched,
            'message': self.message,
            'waiting_for': str(self.waiting_for),
        }

    def user(self):
        return self.message['user']

    def __repr__(self):
        try:
            return advanced_json_encoder.AdvancedJSONEncoder().encode(self.to_json())
        except Exception as err:
            logger.warn(err)
            logger.warn('fail to dump json of message {} '
                        'waiting for {}'.format(str(self.message), str(self.waiting_for)))


def clean_message_data(ctx):
    return utils.safe_set(ctx, 'session', 'data', 'message', {})


def get_user_data(ctx):
    return ctx['session']['data']


def get_message_data(ctx, *args, **kwargs):
    return utils.safe_get(get_user_data(ctx)['message'], *args, **kwargs)


def set_user_data(ctx, data):
    ctx['session']['data'] = {
        **get_user_data(ctx),
        **data,
    }
    return ctx


def set_message_data(ctx, *args):
    return utils.safe_set(ctx, 'session', 'data', 'message', *args)


__all__ = [get_user_data, reducers, set_user_data, StoryContext]
