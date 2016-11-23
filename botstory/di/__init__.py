from . import desciption, inject as inject_module, injector_service

__all__ = []

injector = injector_service.Injector()

bind = injector.bind
clear = injector.clear
desc = desciption.desc
inject = inject_module.inject

__all__.extend([bind, clear, desc, inject])
