import logging

logger = logging.getLogger(__name__)

from . import callable, processor
from .. import matchers


class Undefined:
    """
    Because we can got ever None value we should have something
    that definitely noted that value wasn't defined
    """

    def __init__(self):
        pass


def match_children(data, key, value):
    return [child for child in data['story'].children
            if child.extensions.get(key, Undefined) == value]


class Middleware:
    def __init__(self):
        pass

    def process(self, data, validation_result):
        logger.debug('process_switch data: {}, validation_result: {}'.format(data, validation_result))
        case_story = match_children(data, 'case_id', validation_result)
        if len(case_story) == 0:
            case_story = match_children(data, 'case_equal', validation_result)
        if len(case_story) == 0:
            return data

        logger.debug('got case_story {}'.format(case_story))

        last_stack_item = data['stack_tail'][-1]
        new_stack_item = {
            'step': last_stack_item['step'],
            'topic': last_stack_item['topic'],
            'data': matchers.serialize(callable.WaitForReturn()),
        }

        return {
            'step': 0,
            'story': case_story[0],
            'stack_tail':
                data['stack_tail'][:-1] +
                [new_stack_item, processor.build_empty_stack_item()],  # we are going deeper
        }


@matchers.matcher()
class Switch:
    def __init__(self, cases):
        self.cases = cases

    def validate(self, message):
        for case_id, validator in self.cases.items():
            if validator.validate(message):
                return case_id
        return False

    def serialize(self):
        return [{
                    'id': id,
                    'data': matchers.serialize(c),
                } for id, c in self.cases.items()]

    @staticmethod
    def deserialize(data):
        return Switch({
                          case['id']: matchers.deserialize(case['data'])
                          for case in data
                          })


class SwitchOnValue:
    """
    don't need to wait result
    """
    def __init__(self, value):
        self.value = value
        self.immediately = True


class ForkingStoriesAPI:
    def __init__(self, parser_instance):
        self.parser_instance = parser_instance

    def case(self, match=Undefined, equal_to=Undefined):
        def decorate(story_part):
            compiled_story = self.parser_instance.go_deeper(story_part)
            if match is not Undefined:
                compiled_story.extensions['case_id'] = match
            if equal_to is not Undefined:
                compiled_story.extensions['case_equal'] = equal_to
            return story_part

        return decorate
