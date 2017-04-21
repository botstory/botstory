import inspect

from .parser import camel_case_to_underscore

from .. import di


def inject(t=None):
    def decorated_fn(fn):
        if inspect.isclass(fn):
            name = t or camel_case_to_underscore(fn.__name__)[0]
            print('register {} on name {}'.format(fn, name))
            di.injector.register(name, fn)
        elif inspect.isfunction(fn):
            di.injector.requires(fn)
        else:
            # I'm not sure whether it possible case
            raise NotImplementedError('try decorate {}'.format(fn))
        return fn

    return decorated_fn
