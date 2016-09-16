from .. import matchers


class CommonStoriesAPI:
    def __init__(self, parser_instance, core_instance):
        self.parser_instance = parser_instance
        self.core_instance = core_instance

    def on(self, receive):
        def fn(one_story):
            compiled_story = self.parser_instance.compile(
                one_story,
            )
            compiled_story['validator'] = matchers.get_validator(receive)
            self.core_instance.add_story(compiled_story)

            return one_story

        return fn

    def part(self):
        def fn(part_of_story):
            self.parser_instance.part(part_of_story)
            return part_of_story

        return fn
