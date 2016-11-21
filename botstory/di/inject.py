import inspect

from .parser import camel_case_to_underscore

from .. import di


def inject():
    def decorated_fn(fn):
        if inspect.isclass(fn):
            name = camel_case_to_underscore(fn.__name__)
            di.injector.register(name[0], fn)
        elif inspect.isfunction(fn):
            fn_sig = inspect.signature(fn)
            args = [key for key in fn_sig.parameters.keys() if key != 'self']
            di.injector.requires(fn, args)
        else:
            # I'm not sure whether it possible case
            raise NotImplementedError('try decorate {}'.format(fn))
        return fn

    return decorated_fn
