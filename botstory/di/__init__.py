from . import desciption as desc_module, inject as inject_module, injector_service

__all__ = []

injector = injector_service.Injector()

bind = injector.bind
child_scope = injector.child_scope
clear_instances = injector.clear_instances
desc = desc_module.desc
get = injector.get
inject = inject_module.inject

__all__.extend([bind, child_scope, clear_instances, desc, inject])
