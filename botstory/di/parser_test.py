from .parser import camel_case_to_underscore


def test_():
    assert camel_case_to_underscore('ClassName')[0] == 'class_name'
