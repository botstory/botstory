from botstory import di
import logging
import json
import inspect

logger = logging.getLogger(__name__)


@di.desc(reg=False)
class Parser:
    def __init__(self, library):
        self.current_node = None
        self.current_scope = library.global_scope
        self.middlewares = []

    def compile(self, one_story, middlewares=[]):
        topic = one_story.__name__
        self.middlewares = middlewares
        previous_node = self.current_node
        self.current_node = ASTNode(topic=topic)

        one_story()

        res = self.current_node
        self.current_node = previous_node
        return res

    def compile_scope(self, scope_node, scope_func):
        self.current_node.append(scope_node)
        parent_scope = self.current_scope
        self.current_scope = scope_node.local_scope

        scope_func()

        res = self.current_scope
        self.current_scope = parent_scope
        return res
        # with self.attach_scope():
        #     one_scope()

    def go_deeper(self, one_story, buildScopePart):
        if len(self.current_node.story_line) == 0 or \
                inspect.isfunction(self.current_node.story_line[-1]):
            scope_node = buildScopePart()
            self.current_node.story_line.append(scope_node)
        else:
            scope_node = self.current_node.story_line[-1]

        parent_scope = self.current_scope
        self.current_scope = scope_node.local_scope

        compiled_story = self.compile(one_story, self.middlewares)

        self.current_scope.add(compiled_story)

        self.current_scope = parent_scope

        return compiled_story

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
        # assert isinstance(self.story_line[-1], StoryPartFork)
        self.story_line[-1].add_child(child_story_line)

    def append(self, story_part):
        part_name = story_part.__name__,
        if part_name in self.story_names:
            logger.warning('Already have story with name {}. Please use uniq name'.format(part_name))

        self.story_names.add(part_name)
        self.story_line.append(story_part)

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

    def __call__(self, *args, **kwargs):
        return self.fn(*args, **kwargs)

    def __repr__(self):
        return json.dumps({
            'type': 'StoryPartLeaf',
            'name': self.__name__,
        })
