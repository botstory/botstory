import inspect
from .parser import camel_case_to_underscore
from .. import di


def desc(t=None, reg=True):
    """
    Describe Class Dependency

    :param reg: should we register this class as well
    :param t: custom type as well
    :return:
    """

    def decorated_fn(cls):
        if not inspect.isclass(cls):
            return NotImplemented('For now we can only describe classes')
        name = t or camel_case_to_underscore(cls.__name__)[0]
        if reg:
            di.injector.register(name, cls)
        else:
            di.injector.describe(name, cls)
        return cls

    return decorated_fn
