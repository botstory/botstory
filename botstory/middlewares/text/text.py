class Text:
    class Match:
        def __init__(self, test_string):
            self.test_string = test_string

        def validate(self, message):
            return self.test_string == message.get('text', {}).get('raw', None)
