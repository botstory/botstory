import inspect
from .parser import camel_case_to_underscore
from .. import di


def desc(t=None, lazy=False):
    """
    TODO:
    :param lazy:
    :param t:
    :return:
    """

    def decorated_fn(cls):
        if not inspect.isclass(cls):
            return NotImplemented('For now we can only describe classes')
        name = t or camel_case_to_underscore(cls.__name__)[0]
        if lazy:
            di.injector.describe(name, cls)
        else:
            di.injector.register(name, cls)
        return cls

    return decorated_fn
