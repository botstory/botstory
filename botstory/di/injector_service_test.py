from .. import di


# TODO: should make scoped di
def teardown_function(function):
    di.clear()


def test_injector_get():
    di.injector.register('once_instance', 'Hello World!')
    assert di.injector.get('once_instance') == 'Hello World!'
