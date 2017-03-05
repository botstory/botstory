from botstory.ast import story_context


def test_clean_message_data():
    ctx = {
        'session': {
            'data': {
                'message': {
                    'text': {
                        'raw': 'I\'m going to Mars',
                        'something': 'else',
                    },
                    'location': {
                        'lat': 12,
                        'lng': 21,
                    }
                }
            }
        }
    }
    ctx = story_context.clean_message_data(ctx)
    assert ctx == {
        'session': {
            'data': {
                'message': {
                }
            }
        }
    }


def test_set_message_data():
    ctx = {
        'session': {
            'data': {
                'message': {
                    'text': {
                        'raw': 'I\'m going to Mars',
                        'something': 'else',
                    },
                    'location': {
                        'lat': 12,
                        'lng': 21,
                    }
                }
            }
        }
    }
    ctx = story_context.set_message_data(ctx, 'text', {
        'raw': 'I\'m going to Venus'
    })
    assert ctx == {
        'session': {
            'data': {
                'message': {
                    'text': {
                        'raw': 'I\'m going to Venus',
                    },
                    'location': {
                        'lat': 12,
                        'lng': 21,
                    }
                }
            }
        }
    }
