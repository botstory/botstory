from .. import di


def test_injector_get():
    di.injector.register('once_instance', 'Hello World!')
    assert di.injector.get('once_instance') == 'Hello World!'
