matchers = {}


def build_serializer():
    def default_serialize(_):
        pass

    return default_serialize


def build_deserialize(cls):
    def default_deserialize(data):
        return cls()

    return default_deserialize


def get_validator(receive):
    """
    ask every matcher whether it can serve such filter

    :param receive:
    :return:
    """
    for matcher_type, m in matchers.items():
        if hasattr(m, 'can_handle') and m.can_handle(receive):
            receive = m.handle(receive)

    return receive
    # TODO: should
    # if isinstance(receive, list):
    #     return any.AnyOf([get_validator(r) for r in receive])
    # elif is_string(receive):
    #     return text.Match(receive)
    # else:
    #     return receive


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
