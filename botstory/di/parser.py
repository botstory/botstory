import re


def camel_case_to_underscore(class_name):
    """Converts normal class names into normal arg names.
    Normal class names are assumed to be CamelCase with an optional leading
    underscore.  Normal arg names are assumed to be lower_with_underscores.
    Args:
      class_name: a class name, e.g., "FooBar" or "_FooBar"
    Returns:
      all likely corresponding arg names, e.g., ["foo_bar"]

    based on: <https://github.com/google/pinject/blob/master/pinject/bindings.py>

    """
    parts = []
    rest = class_name
    if rest.startswith('_'):
        rest = rest[1:]
    while True:
        m = re.match(r'([A-Z][a-z]+)(.*)', rest)
        if m is None:
            break
        parts.append(m.group(1))
        rest = m.group(2)
    if not parts:
        return []
    return ['_'.join(part.lower() for part in parts)]


def kebab_to_underscore(s):
    """
    Convert kebab-styled-string to underscore_styled_string
    :param s:
    :return:
    """
    return s.replace('-', '_')
