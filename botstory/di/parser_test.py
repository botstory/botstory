from .parser import camel_case_to_underscore, kebab_to_underscore


def test_camelcase_to_underscore():
    assert camel_case_to_underscore('ClassName')[0] == 'class_name'


def test_remove_leading_underscore():
    assert camel_case_to_underscore('_ClassName')[0] == 'class_name'


def test_should_return_empty_array_if_no_any_class_name_here():
    assert camel_case_to_underscore('_qwerty') == []


def test_kebab_to_underscore():
    assert kebab_to_underscore('hello-world') == 'hello_world'
