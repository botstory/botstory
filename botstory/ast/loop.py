from botstory.ast import library

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
            self.parser_instance.compile_scope(StoriesScopeNode(one_loop), one_loop)
            # TODO: crawl scope for matchers and handlers

            # 1) we already have hierarchy of stories and stack of execution
            # it works that way -- we trying to match request to some story validator
            # by getting story one-by-one from stack

            # 2) we cold add validator for catching all stories from one scope

            # 3) if we didn't match scope we bubble up to previous scope

            # 4) if we match scope-validator we should choose one of its story

            return one_loop

        return fn


class StoriesScopeNode:
    def __init__(self, target):
        self.target = target
        self.local_scope = library.StoriesScope()

    @property
    def __name__(self):
        return self.target.__name__
