from botstory import ast, matchers, middlewares
from botstory.ast import forking
import logging
import json

logger = logging.getLogger(__name__)

# 1. once we trap on StoriesLoopNode we should stop execution
# and wait any user import
# 2. once we got any user import we should come to StoriesLoopNode
# add check whether input match received request.
# 3. execute matched story


class StoryLoopAPI:
    """
    loop (scope) concept similar to switch (forking)
    the main difference is that after case switch jump to the next part
    after last case. But in scope it loop until
    - we get receive unmatched message
    - or break loop explicitly
    """

    def __init__(self, library, parser_instance):
        self.library = library
        self.parser_instance = parser_instance

    def loop(self):
        def fn(one_loop):
            self.parser_instance.compile_scope(
                StoriesLoopNode(one_loop), one_loop)
            # TODO: crawl scope for matchers and handlers

            # 1) we already have hierarchy of stories and stack of execution
            # it works that way -- we trying to match request to some story validator
            # by getting story one-by-one from stack

            # 2) we cold add validator for catching all stories from one scope

            # 3) if we didn't match scope we bubble up to previous scope

            # 4) if we match scope-validator we should choose one of its story

            return one_loop

        return fn


class StoriesLoopNode:
    def __init__(self, target):
        self.target = target
        self.local_scope = ast.library.StoriesScope()

    @property
    def __name__(self):
        return self.target.__name__

    @property
    def children(self):
        return self.local_scope.stories

    def __call__(self, *args, **kwargs):
        return None

    def get_child_by_validation_result(self, topic):
        case_stories = self.local_scope.by_topic(topic)

        if len(case_stories) == 0:
            logger.debug('#######################################')
            logger.debug('# [!] do not have any child here')
            logger.debug('# story node = {}'.format(self))
            logger.debug('# topic = {}'.format(topic))
            logger.debug('#######################################')
            return None

        return case_stories[0]

    def match_children(self, key, value):
        return [child for child in self.local_scope.stories
                if child.extensions.get(key, forking.Undefined) == value]

    def to_json(self):
        return {
            'type': 'StoriesLoopNode',
            'name': self.__name__,
            'local_scope': self.local_scope.to_json()
        }

    def __repr__(self):
        return json.dumps(self.to_json())


@matchers.matcher()
class ScopeMatcher:
    def __init__(self, all_filters):
        # TODO: It's not good name
        # but better what we have for this moment
        # so it could be renamed very soon
        self.new_scope = True
        self.all_filters = all_filters

    def validate(self, message):
        return self.all_filters.validate(message)

    def serialize(self):
        return self.all_filters.serialize()

    def process(self):
        return True

    @classmethod
    def deserialize(cls, data):
        return cls(middlewares.any.AnyOf.deserialize(data))
