matchers = {}


def build_serializer():
    def default_serialize(_):
        pass

    return default_serialize


def build_deserialize(cls):
    def default_deserialize(data):
        return cls()

    return default_deserialize


def matcher():
    def register(m):
        m.type = getattr(m, 'type', m.__name__)
        if not getattr(m, 'serialize', False):
            m.serialize = build_serializer()
        if not getattr(m, 'deserialize', False):
            m.deserialize = build_deserialize(m)
        matchers[m.type] = m
        return m

    return register


def serialize(m):
    return {
        'type': m.type,
        'data': m.serialize(),
    }


def deserialize(data):
    matcher_type = matchers[data['type']]
    return matcher_type.deserialize(data['data'])
