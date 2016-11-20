from .. import di


def test_decorator():
    @di.inject()
    class OneClass:
        def __init__(self):
            pass

    assert isinstance(di.injector.get('one_class'), OneClass)
