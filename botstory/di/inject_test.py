import pytest
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


def test_no_autoupdate_deps_on_new_instance_comes():
    @di.inject()
    class OuterClass:
        @di.inject()
        def inner(self, inner_class=None):
            self.inner_class = inner_class

    outer = di.bind(OuterClass(), autoupdate=False)

    @di.inject()
    class InnerClass:
        pass

    assert isinstance(outer, OuterClass)
    assert outer.inner_class is None


def test_autoupdate_deps_on_new_instance_comes():
    @di.inject()
    class OuterClass:
        @di.inject()
        def inner(self, inner_class=None):
            self.inner_class = inner_class

    outer = di.bind(OuterClass(), autoupdate=True)

    @di.inject()
    class InnerClass:
        pass

    assert isinstance(outer, OuterClass)
    assert isinstance(outer.inner_class, InnerClass)


def test_fail_on_cyclic_deps():
    @di.inject()
    class FirstClass:
        @di.inject()
        def deps(self, second_class=None):
            self.second_class = second_class

    @di.inject()
    class SecondClass:
        @di.inject()
        def deps(self, first_class=None):
            self.first_class = first_class

    first_class = di.injector.get('first_class')
    assert isinstance(first_class.second_class, SecondClass)
    assert isinstance(first_class.second_class.first_class, FirstClass)


def test_custom_type():
    @di.inject('qwerty')
    class OneClass:
        pass

    assert isinstance(di.injector.get('qwerty'), OneClass)


def test_fail_on_incorrect_using():
    with pytest.raises(NotImplementedError):
        di.inject()('qwerty')
