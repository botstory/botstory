from .. import matchers


class CommonStoriesAPI:
    def __init__(self, parser_instance, library):
        self.parser_instance = parser_instance
        self.library = library

    def on(self, receive):
        def fn(one_story):
            compiled_story = self.parser_instance.compile(
                one_story,
            )
            compiled_story.extensions['validator'] = matchers.get_validator(receive)
            self.library.add_message_handler(compiled_story)

            return one_story

        return fn

    def part(self):
        def fn(part_of_story):
            self.parser_instance.part(part_of_story)
            return part_of_story

        return fn
