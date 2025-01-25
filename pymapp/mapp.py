import json
import time
import logging
import weakref
import logging.handlers
import multiprocessing as mp

from .logger_writer import LoggerWriter
from .subprocess_base import SubProcessBase
from .worker_base import WorkerBase
from .register_worker import _registry
from .shared_memory import PyMAppSharedMemory

class MApp():
    def __init__(self, config_filename) -> None:
        with open(config_filename, 'r') as fid:
            self.config = json.load(fid)

        self._log_queue = mp.Queue()
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(logging.DEBUG)
        queue_handler = logging.handlers.QueueHandler(self._log_queue)
        root_logger.addHandler(queue_handler)

        self.logger_writer = LoggerWriter(self._log_queue, self.config["log"])
        self._log_process = SubProcessBase(
            self.logger_writer.run,
            name="log",
        )
        self._log_process.start()
        logging.info(f"Logger initialized")

        self._finalizer = weakref.finalize(self, self._stop)
        self.worker_registry = _registry.workers

        self.manager = mp.Manager()
        self.begin_flag = mp.Event()
        self.stop_flag = mp.Event()

        self.worker_instances: dict[str, WorkerBase] = {}
        self.subprocesses: dict[str, SubProcessBase] = {}
        self.shared_memory: dict[str, PyMAppSharedMemory] = {}

    
    def worker2subprocess(self, worker: WorkerBase, loop_flag: bool):
        return SubProcessBase(
            main_target=worker._worker_run,
            main_loop_flag=loop_flag,
            name=worker.name,
            start_target=worker._worker_start,
            close_target=worker._worker_stop,
            begin_flag=self.begin_flag,
            stop_flag=self.stop_flag,
        )
    
    def create_subprocess(
            self,
            name: str,
            instance: str,
            loop_flag: bool,
            *args,
            **kwargs
    ):
        self.worker_instances[name] = self.worker_registry[instance](
            name,
            self.config[instance],
            self._log_queue,
            *args,
            **kwargs
        )
        self.subprocesses[name] = self.worker2subprocess(
            self.worker_instances[name],
            loop_flag=loop_flag,
        )
    
    def add_shared_memory(
            self,
            name: str,
            size: int,
            workers: list[str],
    ):
        mutex = self.manager.Lock()
        sm = PyMAppSharedMemory(
            name=name,
            size=size,
            create=True,
            mutex=mutex,
            workers=workers,
        )

        for worker in workers:
            if worker not in self.worker_instances.keys():
                raise KeyError(f"Worker {worker} not instantiated in MApp class. Existing instances are {list(self.worker_instances.keys())}")
            self.worker_instances[worker].add_shared_memory(sm)
        self.shared_memory[name] = sm
    
    def start(self):
        for process in self.subprocesses.values():
            process.start()
        all_started = False
        while not all_started:
            all_started = True
            for process in self.subprocesses.values():
                all_started = all_started and process.started_flag.is_set()
        self.begin_flag.set()
    
    def stop(self):
        self._finalizer()

    def _stop(self):
        for process in self.subprocesses.values():
            process: SubProcessBase
            process.stop()
        self.manager.shutdown()
        time.sleep(0.1)
        self._log_process.stop()