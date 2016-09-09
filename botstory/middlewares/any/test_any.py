from . import any
from ... import matchers


def test_serialize_any():
    m_old = any.Any()
    m_new = matchers.deserialize(matchers.serialize(m_old))
    assert isinstance(m_new, any.Any)


def test_serialize_any_of():
    m_old = any.AnyOf([any.Any(), any.Any()])
    m_new = matchers.deserialize(matchers.serialize(m_old))
    assert isinstance(m_new, any.AnyOf)
    assert len(m_new.list_of_matchers) == 2
    assert isinstance(m_new.list_of_matchers[0], any.Any)
    assert isinstance(m_new.list_of_matchers[1], any.Any)
