from botstory import matchers
from botstory.ast import callable, forking
from botstory.ast.story_context import reducers

import json
import logging

logger = logging.getLogger(__name__)


class StoryContext:
    def __init__(self, message, library, waiting_for=None):
        self.library = library
        self.message = message
        self.waiting_for = waiting_for

    def clone(self):
        return StoryContext(self.message,
                            self.library,
                            self.waiting_for)

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
        return self.waiting_for and \
               not isinstance(self.waiting_for, callable.EndOfStory)

    def current_step(self):
        return self.stack_tail()['step']

    def does_it_match_any_story(self):
        return self.compiled_story() is not None

    def is_empty_stack(self):
        return len(self.stack()) == 0

    def is_end_of_story(self):
        return self.current_step() >= len(self.compiled_story().story_line)

    def is_tail_of_story(self):
        return self.current_step() >= len(self.compiled_story().story_line) - 1

    def is_waiting_for_input(self):
        """
        could make one step further
        :return:
        """
        return self.waiting_for and \
               not isinstance(self.waiting_for, forking.SwitchOnValue)

    def get_child_story(self):
        """
        try child story that match message and get scope of it
        :return:
        """
        stack_tail = self.stack_tail()
        story_part = self.compiled_story().story_line[stack_tail['step']]

        if not hasattr(story_part, 'get_child_by_validation_result'):
            return None

        if isinstance(self.waiting_for, forking.SwitchOnValue):
            return story_part.get_child_by_validation_result(self.waiting_for.value)

        if stack_tail['data'] is not None:
            validator = matchers.deserialize(stack_tail['data'])
            validation_result = validator.validate(self.message)
            return story_part.get_child_by_validation_result(validation_result)

        return None

    def get_current_story_part(self):
        return self.compiled_story().story_line[self.current_step()]

    def has_child_story(self):
        return self.get_child_story() is not None

    def stack(self):
        return self.message['session']['stack']

    def stack_tail(self):
        return self.stack()[-1]

    def to_json(self):
        return {
            'message': self.message,
            'waiting_for': str(self.waiting_for),
        }

    def user(self):
        return self.message['user']

    def __repr__(self):
        return json.dumps(self.to_json())


__all__ = [reducers, StoryContext]
