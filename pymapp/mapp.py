import json
import time
import logging
import weakref
import threading
import logging.handlers
import multiprocessing as mp

from .logger_writer import LoggerWriter
from .subprocess_base import SubProcessBase
from .worker_base import WorkerBase
from .registry import _registry
from .shared_memory import PyMAppSharedMemory

class _TestLoad_():
    pass

class MApp():
    def __init__(self, config_location) -> None:

        if isinstance(config_location, _TestLoad_):
            self.config = None

            self._log_queue = None
            self._logger_writer = None
            self._log_process = None

            self._finalizer = None
            self._worker_registry = None
            self._thread = None

            self._manager = None
            self._begin_flag = None
            self._stop_flag = None

            self._worker_instances = None
            self._subprocesses = None
            self._shared_memory = None
        else:
            self._construct(config_location)
    
    def _construct(self, config_location: str):
        with open(config_location, 'r') as fid:
            self.config = json.load(fid)
        self._log_queue = mp.Queue()
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(logging.DEBUG)
        queue_handler = logging.handlers.QueueHandler(self._log_queue)
        root_logger.addHandler(queue_handler)
        self._logger_writer = LoggerWriter(self._log_queue, self.config["log"])
        self._log_process = SubProcessBase(
            self._logger_writer.run,
            name="log",
        )
        self._log_process.start()
        logging.info(f"Logger initialized")

        self._finalizer = weakref.finalize(self, self._mapp_stop)
        self._worker_registry = _registry.workers
        self._thread = threading.Thread(group=None, target=self.run)

        self._manager = mp.Manager()
        self._begin_flag = mp.Event()
        self._stop_flag = mp.Event()

        self._worker_instances: dict[str, WorkerBase] = {}
        self._subprocesses: dict[str, SubProcessBase] = {}
        self._shared_memory: dict[str, PyMAppSharedMemory] = {}

    
    def worker2subprocess(self, worker: WorkerBase, loop_flag: bool):
        return SubProcessBase(
            main_target=worker._worker_run,
            main_loop_flag=loop_flag,
            name=worker.name,
            start_target=worker._worker_start,
            close_target=worker._worker_stop,
            begin_flag=self._begin_flag,
            stop_flag=self._stop_flag,
        )
    
    def create_subprocess(
            self,
            name: str,
            instance: str,
            loop_flag: bool,
            *args,
            **kwargs
    ):
        self._worker_instances[name] = self._worker_registry[instance](
            name,
            self.config[instance],
            self._log_queue,
            *args,
            **kwargs
        )
        self._subprocesses[name] = self.worker2subprocess(
            self._worker_instances[name],
            loop_flag=loop_flag,
        )
    
    def rename_worker(self, current_name:str, new_name:str):
        worker = self._worker_instances[current_name]
        worker.name = new_name
        self._worker_instances[new_name] = worker
        del self._worker_instances[current_name]
        self.restart_subprocess(current_name, new_name)
    
    def restart_subprocess(self, name:str, new_name:str=None):
        if new_name is None:
            new_name = name

        process = self._subprocesses[name]
        process.stop()
        logging.info(f"Stopped subprocess {name}")
        new_process = self.worker2subprocess(
            self._worker_instances[new_name],
            process.main_loop_flag,
        )
        new_process.start()
        logging.info(f"Started subprocess {new_name}")
        return new_process
    
    def add_shared_memory(
            self,
            name: str,
            size: int,
            workers: list[str],
    ):
        mutex = self._manager.Lock()
        sm = PyMAppSharedMemory(
            name=name,
            size=size,
            create=True,
            mutex=mutex,
            workers=workers,
        )

        for worker in workers:
            if worker not in self._worker_instances.keys():
                raise KeyError(f"Worker {worker} not instantiated in MApp class. Existing instances are {list(self._worker_instances.keys())}")
            self._worker_instances[worker].add_shared_memory(sm)
        self._shared_memory[name] = sm
    
    def _start(self):
        for process in self._subprocesses.values():
            process.start()
        all_started = False
        while not all_started:
            all_started = True
            for process in self._subprocesses.values():
                all_started = all_started and process.started_flag.is_set()
        self._begin_flag.set()

    def _watchdog(self):
        time.sleep(self.config["Watchdog"]["check_period_seconds"])

        new_subprocesses = {}
        for name, process in self._subprocesses.items():
            if process.get_heartbeat():
                process.clear_heartbeat()
            else:
                logging.error(f"No heartbeat detected on subprocess {name}")
                new_subprocesses[name] = self.restart_subprocess(name)
                
        
        for name, new_process in new_subprocesses.items():
            new_process : SubProcessBase
            del self._subprocesses[name]
            self._subprocesses[name] = new_process
            logging.info(f"Restarted subprocess {name}")

    def run(self):
        self._start()
        try:
            while not self._stop_flag.is_set():
                self._watchdog()
        except KeyboardInterrupt:
            self._stop()
    
    def _setup(self):
        pass

    def _main(self):
        pass

    def start(self):
        self._setup()
        if not hasattr(self, '_thread'):
            raise AttributeError(f"{self.__class__.__name__} missing '_thread' attribute. Likely due to not being decorated by @pymapp.register_mapp_class(<config_location>)")
        self._thread.start()
        try:
            self._main()
            while True:
                self._thread.join(0)
                time.sleep(0.01)
        except KeyboardInterrupt:
            self._stop()

    def _stop(self):
        self._finalizer()

    def _mapp_stop(self):
        self._stop_flag.set()
        for process in self._subprocesses.values():
            process: SubProcessBase
            process.stop()
        
        for sm in self._shared_memory.values():
            sm.unlink()
        
        self._manager.shutdown()
        time.sleep(0.1)
        self._log_process.stop()