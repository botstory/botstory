matchers = {}


def matcher():
    def register(m):
        m.type = getattr(m, 'type', m.__name__)
        matchers[m.type] = m
        return m

    return register


def serialize(m):
    return {
        'type': m.type,
        'data': m.serialize_data(),
    }


def deserialize(data):
    matcher_type = matchers[data['type']]
    return matcher_type.deserialize(data['data'])
