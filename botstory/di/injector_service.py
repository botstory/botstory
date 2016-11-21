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
        self.requires_fns = {}

    def register(self, type_name, instance):
        self.root.register(type_name, instance)

    def requires(self, fn, requires):
        self.requires_fns[fn] = requires

    def bind(self, instance):
        methods = [
            (m, cls.__dict__[m])
            for cls in inspect.getmro(type(instance))
            for m in cls.__dict__ if inspect.isfunction(cls.__dict__[m])
            ]

        requires_of_methods = [(method_ptr, {dep: self.get(dep) for dep in self.requires_fns.get(method_ptr, [])})
                               for (method_name, method_ptr) in methods]

        for (method_ptr, method_deps) in requires_of_methods:
            if len(method_deps) > 0:
                method_ptr(instance, **method_deps)

        return instance

    def clear(self):
        self.root = Scope()
        self.singleton_cache = {}
        self.requires_fns = {}

    def get(self, type_name):
        try:
            return self.singleton_cache[type_name]
        except KeyError:
            try:
                instance = self.root.get(type_name)
            except KeyError:
                # TODO: sometimes we should fail loudly in this case
                return None

            instance = self.bind(instance)
            self.singleton_cache[type_name] = instance

        return instance
