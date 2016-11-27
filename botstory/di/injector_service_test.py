import pytest
from .. import di


def test_injector_get():
    with di.child_scope():
        di.injector.register('once_instance', 'Hello World!')
        assert di.injector.get('once_instance') == 'Hello World!'


def test_lazy_description_should_not_register_class():
    with di.child_scope():
        @di.desc(reg=False)
        class OneClass:
            pass

        assert di.injector.get('one_class') is None


def test_lazy_description_should_simplify_registration():
    with di.child_scope():
        @di.desc(reg=False)
        class OneClass:
            pass

        di.injector.register(instance=OneClass())

        assert isinstance(di.injector.get('one_class'), OneClass)


def test_not_lazy_description_should_simplify_registration():
    with di.child_scope():
        @di.desc(reg=True)
        class OneClass:
            pass

        assert isinstance(di.injector.get('one_class'), OneClass)


def test_fail_if_type_is_not_string():
    with di.child_scope():
        class OneClass:
            pass

        with pytest.raises(ValueError):
            di.injector.register(OneClass)


def test_kebab_string_style_is_synonym_to_underscore():
    with di.child_scope():
        @di.desc()
        class OneClass:
            pass

        assert isinstance(di.injector.get('one-class'), OneClass)


def test_later_binding():
    with di.child_scope():
        @di.desc()
        class OuterClass:
            @di.inject()
            def deps(self, test_class):
                self.test_class = test_class

        @di.desc('test_class', reg=False)
        class InnerClass:
            pass

        outer = OuterClass()
        di.injector.register(instance=outer)
        di.bind(outer, auto=True)

        inner = InnerClass()
        di.injector.register(instance=inner)

        assert outer.test_class == inner


def test_overwrite_previous_singleton_instance():
    with di.child_scope():
        @di.desc('test_class')
        class FirstClass:
            pass

        first_class = di.get('test_class')

        @di.desc('test_class')
        class SecondClass:
            pass

        second_class = di.get('test_class')

        assert first_class != second_class
        assert isinstance(first_class, FirstClass)
        assert isinstance(second_class, SecondClass)


def test_inherit_scope():
    with di.child_scope('first'):
        @di.desc()
        class First:
            pass

        with di.child_scope('second'):
            @di.desc()
            class Second:
                @di.inject()
                def deps(self, first):
                    self.first = first

            second = di.get('second')
            assert isinstance(second, Second)
            assert isinstance(second.first, First)


def test_do_not_call_deps_endpoint_before_we_have_all_needed_deps():
    with di.child_scope():
        @di.desc()
        class Container:
            def __init__(self):
                self.one = 'undefined'
                self.two = 'undefined'

            @di.inject()
            def deps(self, one, two):
                self.one = one
                self.two = two

        container = di.get('container')
        assert container.one == 'undefined'
        assert container.two == 'undefined'

        @di.desc()
        class One:
            pass

        di.bind(container)
        assert container.one == 'undefined'
        assert container.two == 'undefined'

        @di.desc()
        class Two:
            pass

        di.bind(container)
        assert isinstance(container.one, One)
        assert isinstance(container.two, Two)


def test_do_not_call_deps_endpoint_before_we_have_all_needed_deps_or_default_value():
    with di.child_scope():
        @di.desc()
        class Container:
            def __init__(self):
                self.one = 'undefined'
                self.two = 'undefined'

            @di.inject()
            def deps(self, one, two='default'):
                self.one = one
                self.two = two

        container = di.get('container')
        assert container.one == 'undefined'
        assert container.two == 'undefined'

        @di.desc()
        class One:
            pass

        di.bind(container)
        assert isinstance(container.one, One)
        assert container.two == 'default'

        @di.desc()
        class Two:
            pass

        di.bind(container)
        assert isinstance(container.one, One)
        assert isinstance(container.two, Two)
