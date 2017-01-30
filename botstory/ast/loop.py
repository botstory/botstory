from botstory import ast, matchers, middlewares
import logging
import json

logger = logging.getLogger(__name__)


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
                StoriesScopeNode(one_loop), one_loop)
            # TODO: crawl scope for matchers and handlers

            # 1) we already have hierarchy of stories and stack of execution
            # it works that way -- we trying to match request to some story validator
            # by getting story one-by-one from stack

            # 2) we cold add validator for catching all stories from one scope

            # 3) if we didn't match scope we bubble up to previous scope

            # 4) if we match scope-validator we should choose one of its story

            return one_loop

        return fn


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


class StoriesScopeNode:
    def __init__(self, target):
        self.target = target
        self.local_scope = ast.library.StoriesScope()

    @property
    def __name__(self):
        return self.target.__name__

    def __call__(self, *args, **kwargs):
        return ScopeMatcher(
            middlewares.any.AnyOf(self.local_scope.all_filters())
        )

    def to_json(self):
        return {
            'type': 'StoriesScopeNode',
            'name': self.__name__,
            'local_scope': self.local_scope.to_json()
        }

    def __repr__(self):
        return json.dumps(self.to_json())
