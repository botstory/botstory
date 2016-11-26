from . import desciption as desc_module, inject as inject_module, injector_service

__all__ = []

injector = injector_service.Injector()

bind = injector.bind
desc = desc_module.desc
inject = inject_module.inject
child_scope = injector.child_scope

__all__.extend([bind, child_scope, desc, inject])
