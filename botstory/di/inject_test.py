from .. import di


def teardown_function(function):
    di.clear()


def test_inject_decorator():
    @di.inject()
    class OneClass:
        def __init__(self):
            pass

    assert isinstance(di.injector.get('one_class'), OneClass)


def test_bind_singleton_instance_by_default():
    @di.inject()
    class OneClass:
        def __init__(self):
            pass

    assert di.injector.get('one_class') == di.injector.get('one_class')


def test_inject_into_method_of_class():
    @di.inject()
    class OuterClass:
        @di.inject()
        def inner(self, inner_class):
            self.inner_class = inner_class

    @di.inject()
    class InnerClass:
        pass

    outer = di.injector.get('outer_class')
    assert isinstance(outer, OuterClass)
    assert isinstance(outer.inner_class, InnerClass)


def test_bind_should_inject_deps_in_decorated_methods_():
    @di.inject()
    class OuterClass:
        @di.inject()
        def inner(self, inner_class):
            self.inner_class = inner_class

    @di.inject()
    class InnerClass:
        pass

    outer = di.bind(OuterClass())
    assert isinstance(outer, OuterClass)
    assert isinstance(outer.inner_class, InnerClass)


def test_inject_default_value_if_we_dont_have_dep():
    @di.inject()
    class OuterClass:
        @di.inject()
        def inner(self, inner_class='Hello World!'):
            self.inner_class = inner_class

    outer = di.bind(OuterClass())
    assert isinstance(outer, OuterClass)
    assert outer.inner_class == 'Hello World!'
