import logging
import json
import inspect

logger = logging.getLogger(__name__)


class Parser:
    def __init__(self):
        self.current_node = None
        self.middlewares = []

    def compile(self, one_story, middlewares=[]):
        topic = one_story.__name__
        self.middlewares = middlewares
        self.current_node = ASTNode(topic=topic)

        one_story()

        res = self.current_node
        self.current_node = None
        return res

    def go_deeper(self, one_story):
        if len(self.current_node.story_line) == 0 or \
                inspect.isfunction(self.current_node.story_line[-1]):
            self.current_node.story_line.append(StoryPartFork())

        parent_node = self.current_node
        child_story = self.compile(one_story, self.middlewares)
        parent_node.add_child(child_story)
        self.current_node = parent_node
        return child_story

    def part(self, story_part):
        for m in self.middlewares:
            if hasattr(m, 'process_part') and m.process_part(self, story_part):
                return True

        self.current_node.append(story_part)
        return True

    @property
    def topic(self):
        return self.current_node.topic


class ASTNode:
    def __init__(self, topic):
        self.compiled_story = None
        self.extensions = {}
        self.story_line = []
        self.story_names = set()
        self.topic = topic

    def add_child(self, child_story_line):
        """
        add child node to the last part of story
        :param child_story_line:
        :return:
        """
        assert isinstance(self.story_line[-1], StoryPartFork)
        self.story_line[-1].add_child(child_story_line)

    def append(self, story_part):
        part_name = story_part.__name__,
        if part_name in self.story_names:
            logger.warning('Already have story with name {}. Please use uniq name'.format(part_name))

        self.story_names.add(part_name)
        self.story_line.append(story_part)

    def to_json(self):
        return {
            'type': 'leaf',
            'topic': self.topic,
            'story_names': list(self.story_names),
        }

    def __str__(self):
        return json.dumps(self.to_json())


class StoryPartLeaf:
    def __init__(self, fn):
        self.fn = fn

    def __call__(self, *args, **kwargs):
        return self.fn(*args, **kwargs)

    def __str__(self):
        return {
            'type': 'StoryPartLeaf',
            'name': self.__name__,
        }


class StoryPartFork:
    def __init__(self):
        self.children = []

    def __name__(self):
        return 'StoryPartFork'

    def add_child(self, child_story_line):
        self.children.append(child_story_line)

    def to_json(self):
        return {
            'type': self.__name__,
            'children': list(self.children),
        }

    def __str__(self):
        return json.dumps(self.to_json())
