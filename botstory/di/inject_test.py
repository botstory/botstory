from .. import di


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
