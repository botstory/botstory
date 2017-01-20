from botstory import utils


def test_safe_get_existing_property():
    assert utils.safe_get({
        'a': {
            'b': {
                'c': 'Hello World'
            }
        }
    }, 'a', 'b', 'c') == 'Hello World'


def test_safe_get_unexisting_property():
    assert utils.safe_get({
        'a': {
            'b': {
                'c': 'Hello World'
            }
        }
    }, 'c', 'b', 'a') is None


def test_safe_get_fail_to_default():
    assert utils.safe_get({
        'a': {
            'b': {
                'c': 'Hello World'
            }
        }
    }, 'c', 'b', 'a', default='default-value') == 'default-value'
