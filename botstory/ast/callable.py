from .. import matchers


@matchers.matcher()
class WaitForCallableReturn:
    type = 'WaitForCallableReturn'

    def __init__(self):
        pass

    def validate(self, message):
        return 'return' in message


class CallableNodeWrapper:
    """
    helps start processing callable story
    """

    def __init__(self, ast_node, processor_instance):
        self.ast_node = ast_node
        self.processor_instance = processor_instance

    def startpoint(self, *args, **kwargs):
        if 'session' not in kwargs:
            raise AttributeError('Should pass session as well')

        session = kwargs.pop('session')

        # we are going deeper so prepare one more item in stack
        session.stack.append(None)
        self.processor_instance.process_story(session,
                                              # we don't have message yet
                                              message=None,
                                              compiled_story=self.ast_node.compiled_story,
                                              idx=0,
                                              story_args=args,
                                              story_kwargs=kwargs)

        return WaitForCallableReturn()


class CallableStoriesAPI:
    def __init__(self, library, parser_instance, processor_instance):
        self.library = library
        self.parser_instance = parser_instance
        self.processor_instance = processor_instance

    def callable(self):
        def fn(callable_story):
            compiled_story = self.parser_instance.compile(
                callable_story,
            )
            self.library.add_callable(compiled_story)
            return CallableNodeWrapper(
                compiled_story['parts'],
                self.processor_instance
            ).startpoint

        return fn