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
