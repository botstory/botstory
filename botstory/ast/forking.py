import logging

logger = logging.getLogger(__name__)

from botstory.ast import stack_utils
from . import callable, parser
from .. import matchers


class Undefined:
    """
    Because we can got ever None value we should have something
    that definitely noted that value wasn't defined
    """

    def __init__(self):
        pass


def match_children(data, key, value):
    step_id = data['stack'][-1]['step']
    if step_id >= len(data['story'].story_line):
        return []

    fork = data['story'].story_line[step_id]
    if not isinstance(fork, parser.StoryPartFork):
        return []
    return [child for child in fork.children
            if child.extensions.get(key, Undefined) == value]


class Middleware:
    def __init__(self):
        pass

    def process(self, data, validation_result):
        """
        process switch result before run certain case
        :param data:
        :param validation_result:
        :return:
        """
        logger.debug('process_switch')
        logger.debug('  data: {}'.format(data))
        logger.debug('  validation_result: {}'.format(validation_result))
        # logger.debug('  children len {}'.format(len(data['story'].children)))
        case_stories = match_children(data, 'case_id', validation_result)
        if len(case_stories) == 0:
            case_stories = match_children(data, 'case_equal', validation_result)
        if len(case_stories) == 0:
            case_stories = match_children(data, 'default_case', True)

        if len(case_stories) == 0:
            logger.debug('   do not have any fork here')
            return None

        return case_stories[0]


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


class ForkingStoriesAPI:
    def __init__(self, parser_instance):
        self.parser_instance = parser_instance

    def case(self, default=Undefined, equal_to=Undefined, match=Undefined):
        def decorate(story_part):
            compiled_story = self.parser_instance.go_deeper(story_part)
            if default is True:
                compiled_story.extensions['default_case'] = True
            if equal_to is not Undefined:
                compiled_story.extensions['case_equal'] = equal_to
            if match is not Undefined:
                compiled_story.extensions['case_id'] = match
            return story_part

        return decorate
