import logging
import json

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
        self.children = []
        self.compiled_story = None
        self.extensions = {}
        self.story_line = []
        self.story_names = set()
        self.topic = topic

    def add_child(self, child_story_line):
        self.children.append(child_story_line)

    def append(self, story_part):
        part_name = story_part.__name__,
        if part_name in self.story_names:
            logger.warning('Already have story with name {}. Please use uniq name'.format(part_name))

        self.story_names.add(part_name)
        self.story_line.append(story_part)

    def to_json(self):
        return {
            'topic': self.topic,
            'story_names': list(self.story_names),
        }

    def __str__(self):
        return json.dumps(self.to_json())
