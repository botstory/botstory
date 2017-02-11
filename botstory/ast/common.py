import logging
from .. import matchers, middlewares

logger = logging.getLogger(__name__)


class CommonStoriesAPI:
    def __init__(self, parser, library):
        self.parser = parser
        self.library = library

    def on(self, receive):
        def fn(one_story):
            compiled_story = self.parser.compile(
                one_story,
            )
            compiled_story.extensions['validator'] = matchers.get_validator(receive)
            self.parser.current_scope.add(compiled_story)

            return one_story

        return fn

    def on_start(self):
        def fn(one_story):
            compiled_story = self.parser.compile(
                one_story,
            )
            compiled_story.extensions['validator'] = middlewares.option.OnStart()
            self.library.add_global(compiled_story)

            return one_story

        return fn

    def part(self):
        def fn(part_of_story):
            self.parser.part(part_of_story)
            return part_of_story

        return fn
