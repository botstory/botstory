class StoriesScope:
    def __init__(self, library):
        self.library = library

    def scope(self):
        def fn(one_scope):
            # TODO: crawl scope for matchers and handlers

            # 1) we already have hierarchy of stories and stack of execution
            # it works that way -- we trying to match request to some story validator
            # by getting story one-by-one from stack

            # 2) we cold add validator for catching all stories from one scope

            # 3) if we didn't match scope we bubble up to previous scope

            # 4) if we match scope-validator we should choose one of its story

            return one_scope

        return fn
