from ... import matchers


@matchers.matcher()
class Any:
    def __init__(self):
        pass

    def validate(self, message):
        return True


@matchers.matcher()
class AnyOf:
    def __init__(self, list_of_matchers):
        self.list_of_matchers = list_of_matchers

    def validate(self, message):
        return len(
            [m for m in self.list_of_matchers if m.validate(message)]
        ) > 0

    def serialize(self):
        return [matchers.serialize(m) for m in self.list_of_matchers]

    @staticmethod
    def deserialize(data):
        return AnyOf([matchers.deserialize(d) for d in data])

    @staticmethod
    def can_handle(data):
        return isinstance(data, list)

    @staticmethod
    def handle(data):
        return AnyOf([matchers.get_validator(r) for r in data])
