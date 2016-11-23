from .. import di


# TODO: should make scoped di
def teardown_function(function):
    di.clear()


def test_injector_get():
    di.injector.register('once_instance', 'Hello World!')
    assert di.injector.get('once_instance') == 'Hello World!'


def test_lazy_description_should_not_register_class():
    @di.desc(lazy=True)
    class OneClass:
        pass

    assert di.injector.get('one_class') is None


def test_lazy_description_should_simplify_registration():
    @di.desc(lazy=True)
    class OneClass:
        pass

    di.injector.register(instance=OneClass())

    assert isinstance(di.injector.get('one_class'), OneClass)


def test_not_lazy_description_should_simplify_registration():
    @di.desc(lazy=False)
    class OneClass:
        pass

    assert isinstance(di.injector.get('one_class'), OneClass)