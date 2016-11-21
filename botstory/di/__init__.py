from .injector_service import Injector
from .inject import inject

__all__ = []

injector = Injector()
bind = injector.bind
clear = injector.clear

__all__.extend([bind, clear, inject])
