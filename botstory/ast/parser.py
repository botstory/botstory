import logging

logger = logging.getLogger(__name__)


class Parser:
    def __init__(self):
        self.node = None
        self.middlewares = []

    def compile(self, one_story, middlewares=[]):
        topic = one_story.__name__
        self.middlewares = middlewares
        self.node = ASTNode(topic=topic)

        one_story()

        compiled_story = {
            'topic': topic,
            'parts': self.node,
        }

        self.node.compiled_story = compiled_story

        self.node = None
        return compiled_story

    def part(self, story_part):
        for m in self.middlewares:
            if hasattr(m, 'process_part') and m.process_part(self, story_part):
                return True

        self.node.append(story_part)
        return True

    @property
    def topic(self):
        return self.node.topic


class ASTNode:
    def __init__(self, topic):
        self.compiled_story = None
        self.story_line = []
        self.story_names = set()
        self.topic = topic

    def append(self, story_part):
        part_name = story_part.__name__,
        if part_name in self.story_names:
            logger.warning('Already have story with name {}. Please use uniq name'.format(part_name))

        self.story_names.add(part_name)
        self.story_line.append(story_part)
