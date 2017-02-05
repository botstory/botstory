from botstory import matchers
import logging
import json

logger = logging.getLogger(__name__)


class Undefined:
    """
    Because we can got ever None value we should have something
    that definitely noted that value wasn't defined
    """

    def __init__(self):
        pass


class StoryPartFork:
    def __init__(self):
        self.children = []

    @classmethod
    def factory(cls):
        return cls()

    @property
    def __name__(self):
        return 'StoryPartFork'

    def __call__(self, *args, **kwargs):
        return None

    def add_child(self, child_story_line):
        self.children.append(child_story_line)

    def get_child_by_validation_result(self, validation_result):
        case_stories = self.match_children('case_id', validation_result)
        if len(case_stories) == 0:
            case_stories = self.match_children('case_equal', validation_result)
        if len(case_stories) == 0:
            case_stories = self.match_children('default_case', True)

        if len(case_stories) == 0:
            logger.debug('   do not have any fork here')
            return None

        return case_stories[0]

    def match_children(self, key, value):
        return [child for child in self.children
                if child.extensions.get(key, Undefined) == value]

    def to_json(self):
        return {
            'type': 'StoryPartFork',
            'children': list(map(lambda c: c.to_json(), self.children))
        }

    def __repr__(self):
        return json.dumps(self.to_json())


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
            compiled_story = self.parser_instance.go_deeper(story_part, StoryPartFork.factory)
            if default is True:
                compiled_story.extensions['default_case'] = True
            if equal_to is not Undefined:
                compiled_story.extensions['case_equal'] = equal_to
            if match is not Undefined:
                compiled_story.extensions['case_id'] = match
            return story_part

        return decorate
