from ... import matchers


@matchers.matcher()
class Any:
    def __init__(self):
        pass

    def validate(self, message):
        return True

    def serialize_data(self):
        return None

    @staticmethod
    def deserialize(data):
        return Any()


@matchers.matcher()
class AnyOf:
    def __init__(self, list_of_matchers):
        self.list_of_matchers = list_of_matchers

    def validate(self, message):
        return len(
            [m for m in self.list_of_matchers if m.validate(message)]
        ) > 0

    def serialize_data(self):
        return [matchers.serialize(m) for m in self.list_of_matchers]

    @staticmethod
    def deserialize(data):
        return AnyOf([matchers.deserialize(d) for d in data])
