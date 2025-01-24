import traceback

from .worker_base import WorkerBase

class WorkerRegistry:
    def __init__(self):
        self.workers = {}
        self.start_methods = {}
        self.stop_methods = {}
        self.run_methods = {}

    def register_class(self):
        def make_worker(cls):
            original_init = cls.__init__
            def __init__(cls_self, name, config, log_queue, queues, values, *args, **kwargs):
                cls_self.name = name
                cls_self.config = config
                cls_self._log_queue = log_queue
                cls_self.queues = queues
                cls_self.values = values
                original_init(cls_self, *args, **kwargs)
            cls.__init__ = __init__

            cls._setup_log = WorkerBase._setup_log
            cls._stop_log = WorkerBase._stop_log
            if cls.__name__ in self.start_methods:
                cls._registered_start = self.start_methods[cls.__name__]
            else:
                cls._registered_start = WorkerBase._pass

            if cls.__name__ in self.stop_methods:
                cls._registered_stop = self.stop_methods[cls.__name__]
            else:
                cls._registered_stop = WorkerBase._pass

            if cls.__name__ in self.run_methods:
                cls._registered_run = self.run_methods[cls.__name__]
            else:
                raise RuntimeError(f'Registered worker {cls.__name__} has no main method decorated by @pymapp.run_method')


            cls._worker_start = WorkerBase._worker_start
            cls._worker_stop = WorkerBase._worker_stop
            cls._worker_run = WorkerBase._worker_run

            self.workers[cls.__name__] = cls
            return cls
        return make_worker

    def register_method(self, method_type):
        def decorator(func):
            cls_name = func.__qualname__.split('.')[0]
            if method_type == 'start':
                self.start_methods[cls_name] = func
            elif method_type == 'stop':
                self.stop_methods[cls_name] = func
            else:
                self.run_methods[cls_name] = func
            def wrapper(*args, **kwargs):
                # for worker_cls in self.workers.values():
                #     if isinstance(args[0], worker_cls):
                #         print('a', args[0])
                retval = func(*args, **kwargs)
                return retval
            return wrapper
        return decorator


    def get_class(self, name):
        return self.workers.get(name)

_registry = WorkerRegistry()

def register():
    return _registry.register_class()

def start_method():
    return _registry.register_method('start')

def stop_method():
    return _registry.register_method('stop')

def run_method():
    return _registry.register_method('run')
