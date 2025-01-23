
class WorkerRegistry:
    def __init__(self):
        self.workers = {}

    def register(self):
        def decorator(cls):
            self.workers[cls.__name__] = cls
            return cls
        return decorator

    def get_class(self, name):
        return self.workers.get(name)

_registry = WorkerRegistry()

def register():
    return _registry.register()


