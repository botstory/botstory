class Text:
    class Match:
        type = 'text.match'

        def __init__(self, test_string):
            self.test_string = test_string

        def validate(self, message):
            return self.test_string == (message.text and message.text.get('raw', None))

        def serialize(self):
            return self.test_string

        def deserialize(self, state):
            self.test_string = state
