import warnings
import traceback

import pymapp

def do_nothing(*args, **kwargs):
    pass

class MAppRegistry:
    def __init__(self):
        self.workers = {}
        self.worker_start_methods = {}
        self.worker_stop_methods = {}
        self.worker_run_methods = {}
        self.worker_message_handler_methods = {}
        self.message_queues = None
        self.main_method = None
        self.setup_method = do_nothing
    
    def register_mapp_class(self, config_location):
        def make_mapp_class(cls):
            original_init = cls.__init__
            def __init__(cls_self, *args, **kwargs):
                original_init(cls_self, *args, **kwargs)

                temp = pymapp.MApp(pymapp.mapp._TestLoad_())
                mapp_attribs = {x for x in dir(temp) if x[:2] != "__"}
                for key in cls_self.__dict__.keys():
                    if key in mapp_attribs:
                        warnings.warn(f"Attribute '{key}' in '{cls.__name__}' would be overridden by PyMApp. Consider using a different name.")
                        
                cls_self._construct(config_location)
                self.message_queues = cls_self._message_queues
            
            method_attribs = {x for x in dir(pymapp.MApp) if x[:2] != "__"}
            for attrib in method_attribs:
                setattr(cls, attrib, getattr(pymapp.MApp, attrib))
            cls.__init__ = __init__

            cls._main = self.main_method

            if self.setup_method == do_nothing:
                warnings.warn('No setup method defined. Use @pymapp.register_setup_method() to define code for setup. doing nothing.')
            else:
                cls._setup = self.setup_method

            return cls
        return make_mapp_class

    def register_worker(self):
        def make_worker(cls):
            original_init = cls.__init__
            def __init__(cls_self, name, config, log_queue, message_queue, sender_queues, *args, **kwargs):
                cls_self.name = name
                cls_self.config = config
                cls_self._log_queue = log_queue
                cls_self._message_queue = message_queue
                cls_self._sender_queues = sender_queues
                cls_self.shared_memory = {}
                original_init(cls_self, *args, **kwargs)
            cls.__init__ = __init__

            cls.add_shared_memory = pymapp.WorkerBase.add_shared_memory
            cls._setup_log = pymapp.WorkerBase._setup_log
            cls._stop_log = pymapp.WorkerBase._stop_log
            if cls.__name__ in self.worker_start_methods:
                cls._registered_start = self.worker_start_methods[cls.__name__]
            else:
                cls._registered_start = do_nothing#pymapp.WorkerBase._pass

            if cls.__name__ in self.worker_stop_methods:
                cls._registered_stop = self.worker_stop_methods[cls.__name__]
            else:
                cls._registered_stop = do_nothing#pymapp.WorkerBase._pass

            if cls.__name__ in self.worker_run_methods:
                cls._registered_run = self.worker_run_methods[cls.__name__]
            else:
                raise RuntimeError(f'Registered worker {cls.__name__} has no main method decorated by @pymapp.run_method')
            
            if cls.__name__ in self.worker_message_handler_methods:
                cls._registered_message_handler = self.worker_message_handler_methods[cls.__name__]
            else:
                warnings.warn(f'Registered worker {cls.__name__} has no message handler decorated by @pymapp.message_handler_method')


            cls._worker_start = pymapp.WorkerBase._worker_start
            cls._worker_stop = pymapp.WorkerBase._worker_stop
            cls._worker_run = pymapp.WorkerBase._worker_run

            self.workers[cls.__name__] = cls
            return cls
        return make_worker

    def register_method(self, method_type):
        def decorator(func):
            cls_name = func.__qualname__.split('.')[0]
            if method_type == 'start':
                self.worker_start_methods[cls_name] = func
            elif method_type == 'stop':
                self.worker_stop_methods[cls_name] = func
            elif method_type == 'run':
                self.worker_run_methods[cls_name] = func
            elif method_type == 'message_handler':
                self.worker_message_handler_methods[cls_name] = func
            elif method_type == 'main':
                self.main_method = func
            elif method_type == 'setup':
                self.setup_method = func
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

_registry = MAppRegistry()

def register_mapp_class(config_location):
    return _registry.register_mapp_class(config_location)

def register_main_method():
    return _registry.register_method('main')

def register_setup_method():
    return _registry.register_method('setup')

def register_worker():
    return _registry.register_worker()

def start_method():
    return _registry.register_method('start')

def stop_method():
    return _registry.register_method('stop')

def run_method():
    return _registry.register_method('run')

def message_handler_method():
    return _registry.register_method('message_handler')
