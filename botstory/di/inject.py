from inspect import signature

from .parser import camel_case_to_underscore

from .. import di


def inject():
    def decorated_fn(fn):
        fn_sig = signature(fn)
        di.injector.register(camel_case_to_underscore(fn.__name__)[0], fn)
        return fn

    return decorated_fn
