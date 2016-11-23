from . import desciption as desc_module, inject as inject_module, injector_service

__all__ = []

injector = injector_service.Injector()

bind = injector.bind
clear = injector.clear
desc = desc_module.desc
inject = inject_module.inject

__all__.extend([bind, clear, desc, inject])
