import logging

logger = logging.getLogger(__name__)

from . import callable
from .. import matchers


class Middleware:
    def __init__(self):
        pass

    def process(self, data, validation_result):
        logger.debug('process_switch data: {}, validation_result: {}'.format(data, validation_result))
        logger.debug([child.extensions['case_id'] for child in data['story'].children])
        case_story = [
            child for child in data['story'].children
            if child.extensions['case_id'] == validation_result
            ]

        logger.debug('got case_story {}'.format(case_story))

        if not case_story or len(case_story) == 0:
            return data

        last_stack_item = data['stack_tail'][-1]
        new_stack_item = {
            'step': last_stack_item['step'],
            'topic': last_stack_item['topic'],
            'data': matchers.serialize(callable.WaitForReturn()),
        }

        return {
            'step': 0,
            'story': case_story,
            'stack_tail': data['stack_tail'][:-1] + [new_stack_item, None],  # we are going deeper
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


class ForkingStoriesAPI:
    def __init__(self, parser_instance):
        self.parser_instance = parser_instance

    def case(self, match):
        def decorate(story_part):
            compiled_story = self.parser_instance.go_deeper(story_part)
            compiled_story.extensions['case_id'] = match
            return story_part

        return decorate
