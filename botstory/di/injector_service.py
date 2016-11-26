import inspect

from . import parser


class Scope:
    def __init__(self):
        self.storage = {}
        # instances that will auto update on each new instance come
        self.auto_update_list = []
        # description of classes
        self.described = {}
        # functions that waits for deps
        self.requires_fns = {}
        # all instances that are singletones
        self.singleton_cache = {}

    def get(self, type_name):
        item = self.storage[type_name]
        if inspect.isclass(item):
            return item()
        else:
            return item

    def clear(self):
        self.auto_update_list = []
        self.described = {}
        self.requires_fns = {}
        self.singleton_cache = {}

    def register(self, type_name, value):
        self.storage[type_name] = value


def null_if_empty(value):
    return value if value is not inspect.Parameter.empty else None


class MissedDescriptionError(Exception):
    pass


class Injector:
    def __init__(self):
        self.root = Scope()
        self.current_scope = self.root

    def describe(self, type_name, cls):
        """
        add description of class

        :param type_name:
        :param cls:
        :return:
        """

        self.current_scope.described[cls] = {
            'type': type_name,
        }

    def register(self, type_name=None, instance=None):
        print()
        print('register {} = {}'.format(type_name, instance))
        if not isinstance(type_name, str) and type_name is not None:
            raise ValueError('type_name parameter should be string or None')
        if type_name is None:
            try:
                desc = self.current_scope.described.get(instance, self.current_scope.described[type(instance)])
            except KeyError:
                # TODO: should raise exception
                # raise MissedDescriptionError('{} was not registered'.format(instance))
                # print('self.described')
                # print(self.current_scope.described)
                # print('type(instance)')
                # print(type(instance))
                # print('self.described.get(type(instance))')
                # print(self.current_scope.described.get(type(instance)))
                print('{} was not registered'.format(instance))
                return None
            type_name = desc['type']
        # print('> before store {} = {}'.format(type_name, instance))
        self.current_scope.register(type_name, instance)
        for wait_instance in self.current_scope.auto_update_list:
            self.bind(wait_instance)

    def requires(self, fn):
        fn_sig = inspect.signature(fn)
        self.current_scope.requires_fns[fn] = {
            key: {'default': null_if_empty(fn_sig.parameters[key].default)}
            for key in fn_sig.parameters.keys() if key != 'self'}

    def bind(self, instance, autoupdate=False):
        methods = [
            (m, cls.__dict__[m])
            for cls in inspect.getmro(type(instance))
            for m in cls.__dict__ if inspect.isfunction(cls.__dict__[m])
            ]

        # print('methods')
        # print(methods)

        requires_of_methods = [(method_ptr, {dep: self.get(dep) or dep_spec['default']
                                             for dep, dep_spec in
                                             self.current_scope.requires_fns.get(method_ptr, {}).items()})
                               for (method_name, method_ptr) in methods]

        # print('requires_of_methods')
        # print(requires_of_methods)

        for (method_ptr, method_deps) in requires_of_methods:
            if len(method_deps) > 0:
                method_ptr(instance, **method_deps)

        if autoupdate and instance not in self.current_scope.auto_update_list:
            self.current_scope.auto_update_list.append(instance)

        return instance

    def get(self, type_name):
        type_name = parser.kebab_to_underscore(type_name)
        try:
            return self.current_scope.singleton_cache[type_name]
        except KeyError:
            try:
                instance = self.current_scope.get(type_name)
            except KeyError:
                # TODO: sometimes we should fail loudly in this case
                return None

            self.current_scope.singleton_cache[type_name] = instance
            instance = self.bind(instance)

        return instance

    def child_scope(self):
        return ChildScopeBuilder(self)

    def add_scope(self, scope):
        self.current_scope = scope

    def remove_scope(self, scope):
        assert self.current_scope == scope
        self.current_scope = self.root


class ChildScopeBuilder:
    def __init__(self, injector):
        self.injector = injector

    def __enter__(self):
        self.scope = Scope()
        self.injector.add_scope(self.scope)
        return self.scope

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.scope.clear()
        self.injector.remove_scope(self.scope)
