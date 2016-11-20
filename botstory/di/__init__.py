from .injector_service import Injector
from .inject import inject

__all__ = []

injector = Injector()

__all__.extend([inject])
