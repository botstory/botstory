import inspect
from .parser import camel_case_to_underscore
from .. import di


def desc(lazy=False, t=None):
    """
    TODO:
    :param lazy:
    :param t:
    :return:
    """

    def decorated_fn(fn):
        if not inspect.isclass(fn):
            return NotImplemented('For now we can only describe classes')
        name = t or camel_case_to_underscore(fn.__name__)[0]
        if lazy:
            di.injector.describe(name, fn)
        else:
            di.injector.register(name, fn)
        return fn

    return decorated_fn
