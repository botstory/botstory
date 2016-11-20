class Scope:
    def __init__(self):
        self.storage = {}

    def get(self, type_name):
        return self.storage[type_name]

    def register(self, type_name, value):
        self.storage[type_name] = value


class Injector:
    def __init__(self):
        self.root = Scope()

    def register(self, type_name, instance):
        self.root.register(type_name, instance)

    def get(self, type_name):
        return self.root.get(type_name)
