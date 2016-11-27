import logging
import inspect

from . import parser

logger = logging.getLogger(__name__)


class Scope:
    def __init__(self, name, parent=None):
        self.storage = {}
        # instances that will auto update on each new instance come
        self.auto_bind_list = []
        # description of classes
        self.described = {}
        # functions that waits for deps
        self.requires_fns = {}
        # all instances that are singletones
        self.singleton_cache = {}
        self.name = name
        # parent scope
        self.parent = parent

    def get(self, type_name):
        try:
            item = self.storage[type_name]
            if inspect.isclass(item):
                return item()
            else:
                return item
        except KeyError as err:
            if self.parent:
                return self.parent.get(type_name)
            raise err

    def get_instance(self, type_name):
        try:
            return self.singleton_cache[type_name]
        except KeyError as err:
            if self.parent:
                return self.parent.get_instance(type_name)
            raise err

    def describe(self, type_name, cls):
        self.described[cls] = {
            'type': type_name,
        }

    def get_auto_bind_list(self):
        yield from self.auto_bind_list
        if self.parent:
            yield from self.parent.get_auto_bind_list()

    def auto_bind(self, instance):
        self.auto_bind_list.append(instance)

    def get_description(self, value):
        try:
            return self.described.get(value, self.described[type(value)])
        except KeyError as err:
            if self.parent:
                return self.parent.get_description(value)
            raise err

    def store_instance(self, type_name, instance):
        self.singleton_cache[type_name] = instance

    def get_endpoint_deps(self, method_ptr):
        return self.requires_fns.get(method_ptr, {}).items() or \
               self.parent and self.parent.get_endpoint_deps(method_ptr) or \
               []

    def store_deps_endpoint(self, fn, deps):
        self.requires_fns[fn] = deps

    def clear(self):
        self.auto_bind_list = []
        self.described = {}
        self.requires_fns = {}
        self.singleton_cache = {}

    def clear_instances(self):
        self.auto_bind_list = []
        self.singleton_cache = {}
        self.storage = {}

    def register(self, type_name, value):
        if type_name in self.storage:
            self.remove_type(type_name)

        self.storage[type_name] = value

    def remove_type(self, type_name):
        self.storage.pop(type_name, True)
        instance = self.singleton_cache.pop(type_name, True)
        # TODO: clear self.requires_fns and self.auto_update_list maybe we can use type(instance)?

    def __repr__(self):
        return '<Scope {}> {}'.format(self.name, {
            'storage': self.storage,
            'auto_update_list': self.auto_bind_list,
            'described': self.described,
            'requires_fns': self.requires_fns,
            'singleton_cache': self.singleton_cache,
        })


def empty_array_if_empty(default):
    return [default] if default is not inspect.Parameter.empty else []


class MissedDescriptionError(Exception):
    pass


class Injector:
    def __init__(self):
        self.root = Scope('root')
        self.current_scope = self.root

    def describe(self, type_name, cls):
        """
        add description of class

        :param type_name:
        :param cls:
        :return:
        """

        self.current_scope.describe(type_name, cls)

    def register(self, type_name=None, instance=None):
        print()
        print('register {} = {}'.format(type_name, instance))
        if not isinstance(type_name, str) and type_name is not None:
            raise ValueError('type_name parameter should be string or None')
        if type_name is None:
            try:
                desc = self.current_scope.get_description(instance)
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
        for wait_instance in self.current_scope.get_auto_bind_list():
            self.bind(wait_instance)

    def requires(self, fn):
        fn_sig = inspect.signature(fn)
        self.current_scope.store_deps_endpoint(fn, {
            key: {'default': default for default in empty_array_if_empty(fn_sig.parameters[key].default)}
            for key in fn_sig.parameters.keys() if key != 'self'})

    def entrypoint_deps(self, method_ptr):
        # we should have something to inject
        # registered instance, class or default value
        if not any(self.get(dep) or 'default' in dep_spec
                   for dep, dep_spec
                   in self.current_scope.get_endpoint_deps(method_ptr)):
            # otherwise we should inject anything
            return {}

        return {dep: self.get(dep) or dep_spec['default']
                for dep, dep_spec in self.current_scope.get_endpoint_deps(method_ptr)}

    def bind(self, instance, auto=False):
        """
        Bind deps to instance

        :param instance:
        :param auto: follow update of DI and refresh binds once we will get something new
        :return:
        """
        methods = [
            (m, cls.__dict__[m])
            for cls in inspect.getmro(type(instance))
            for m in cls.__dict__ if inspect.isfunction(cls.__dict__[m])
            ]

        try:
            deps_of_endpoints = [(method_ptr, self.entrypoint_deps(method_ptr))
                                 for (method_name, method_ptr) in methods]

            for (method_ptr, method_deps) in deps_of_endpoints:
                if len(method_deps) > 0:
                    method_ptr(instance, **method_deps)
        except KeyError:
            pass

        if auto and instance not in self.current_scope.get_auto_bind_list():
            self.current_scope.auto_bind(instance)

        return instance

    def get(self, type_name):
        type_name = parser.kebab_to_underscore(type_name)
        try:
            return self.current_scope.get_instance(type_name)
        except KeyError:
            try:
                instance = self.current_scope.get(type_name)
            except KeyError:
                # TODO: sometimes we should fail loudly in this case
                return None

            self.current_scope.store_instance(type_name, instance)
            instance = self.bind(instance)

        return instance

    def child_scope(self, name='undefined'):
        return ChildScopeBuilder(self, self.current_scope, name)

    def clear_instances(self):
        self.current_scope.clear_instances()

    def add_scope(self, scope):
        self.current_scope = scope

    def remove_scope(self, scope):
        assert self.current_scope == scope
        self.current_scope = scope.parent


class ChildScopeBuilder:
    def __init__(self, injector, parent, name):
        self.injector = injector
        self.name = name
        self.parent = parent

    def __enter__(self):
        self.scope = Scope(self.name, self.parent)
        self.injector.add_scope(self.scope)
        return self.scope

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.scope.clear()
        self.injector.remove_scope(self.scope)
