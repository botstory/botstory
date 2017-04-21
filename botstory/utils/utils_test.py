from botstory import utils


def test_safe_get_existing_property():
    assert utils.safe_get({
        'a': {
            'b': {
                'c': 'Hello World'
            }
        }
    }, 'a', 'b', 'c') == 'Hello World'


def test_safe_get_nonexistent_property():
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


def test_safe_get_of_none_is_none():
    assert utils.safe_get(None, 'c', 'b', 'a') is None


def test_safe_get_of_dict_with_none():
    assert utils.safe_get({
        'c': None
    }, 'c', 'b', 'a') is None


def test_safe_set_existing_property():
    assert utils.safe_set({
        'a': {
            'b': {
                'c': 'Mercury',
            }
        }
    }, 'a', 'b', 'c', 'Venus') == {
               'a': {
                   'b': {
                       'c': 'Venus',
                   }
               }
           }


def test_safe_set_nonexistent_property():
    assert utils.safe_set({
        'a': {
            'b': {
                'c': 'Mercury',
            }
        }
    }, 'a', 'b2', 'c2', 'Venus') == {
               'a': {
                   'b': {
                       'c': 'Mercury',
                   },
                   'b2': {
                       'c2': 'Venus',
                   }
               }
           }


def test_safe_set_updates_by_dict():
    assert utils.safe_set({
        'planets': {
            'Mercury': {
                'gravity': 3.7,
                'mass': 0.055,
                'radius': 2440,
            },
            'Venus': {
                'gravity': 8.87,
                'mass': 0.815,
                'radius': 6052,
            },
            'Earth': {
                'error': 'missed',
            }
        }
    }, 'planets', 'Earth', {
        'gravity': 9.8,
        'radius': 6371,
        'mass': 1,
    }) == {
           'planets': {
               'Mercury': {
                   'gravity': 3.7,
                   'mass': 0.055,
                   'radius': 2440,
               },
               'Venus': {
                   'gravity': 8.87,
                   'mass': 0.815,
                   'radius': 6052,
               },
               'Earth': {
                   'gravity': 9.8,
                   'radius': 6371,
                   'mass': 1,
               }
           }
       }
