from botstory import di
import logging
import json

logger = logging.getLogger(__name__)


@di.desc(reg=False)
class Parser:
    def __init__(self, library):
        self.current_node = None
        self.current_scope = library.global_scope

    def compile(self, one_story):
        topic = one_story.__name__
        previous_node = self.current_node
        self.current_node = ASTNode(topic=topic)

        one_story()

        res = self.current_node
        self.current_node = previous_node
        return res

    def compile_fork(self, fork_node, one_story):
        parent_scope = self.current_scope
        self.current_scope = fork_node.local_scope

        compiled_story = self.compile(one_story)

        self.current_scope.add(compiled_story)

        self.current_scope = parent_scope

        return compiled_story

    def compile_scope(self, scope_node, scope_func):
        parent_scope = self.current_scope
        self.current_scope = scope_node.local_scope

        scope_func()

        res = self.current_scope
        self.current_scope = parent_scope
        return res

    def get_last_story_part(self):
        return self.current_node.story_line[-1] \
            if len(self.current_node.story_line) > 0 else None

    def add_to_current_node(self, node):
        self.current_node.append(node)

    def part(self, story_part):
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
        # assert isinstance(self.story_line[-1], StoryPartFork)
        self.story_line[-1].add_child(child_story_line)

    def append(self, story_part):
        part_name = story_part.__name__,
        if part_name in self.story_names:
            logger.warning('Already have story with name {}. Please use uniq name'.format(part_name))

        self.story_names.add(part_name)
        self.story_line.append(story_part)
        return story_part

    def to_json(self):
        return {
            'type': 'ASTNode',
            'topic': self.topic,
            'story_line': list(
                [l.to_json() if hasattr(l, 'to_json') else 'part: {}'.format(l.__name__) for l in self.story_line]
            ),
        }

    def __repr__(self):
        return json.dumps(self.to_json())


class StoryPartLeaf:
    def __init__(self, fn):
        self.fn = fn

    @property
    def __name__(self):
        return self.fn.__name__

    def __call__(self, *args, **kwargs):
        # TODO: because we could have async and sync parts
        # we should check it here
        return self.fn(*args, **kwargs)

    def __repr__(self):
        return json.dumps({
            'type': 'StoryPartLeaf',
            'name': self.__name__,
        })
