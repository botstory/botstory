import inspect


class Scope:
    def __init__(self):
        self.storage = {}

    def get(self, type_name):
        item = self.storage[type_name]
        if inspect.isclass(item):
            return item()
        else:
            return item

    def register(self, type_name, value):
        self.storage[type_name] = value


class Injector:
    def __init__(self):
        self.root = Scope()
        self.singleton_cache = {}

    def register(self, type_name, instance):
        self.root.register(type_name, instance)

    def get(self, type_name):
        try:
            return self.singleton_cache[type_name]
        except KeyError:
            instance = self.root.get(type_name)
            self.singleton_cache[type_name] = instance
            return instance
