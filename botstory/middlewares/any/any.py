class Any:
    type = 'any'

    def __init__(self):
        pass

    def validate(self, message):
        return True

    def serialize(self):
        return None

    def deserialize(self, state):
        pass
