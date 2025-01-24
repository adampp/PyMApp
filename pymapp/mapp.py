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

        self.worker_instances: dict[str, WorkerBase] = {}
        self.subprocesses: dict[str, SubProcessBase] = {}

        self.begin_flag = mp.Event()
        self.stop_flag = mp.Event()
    
    def worker2subprocess(self, worker: WorkerBase, loop_flag: bool, *args, **kwargs):
        return SubProcessBase(
            main_target=worker._worker_run,
            main_loop_flag=loop_flag,
            args=args,
            kwargs=kwargs,
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
            queues: dict[str, mp.Queue],
            values: dict[str, object],
            *args,
            **kwargs
    ):
        self.worker_instances[name] = self.worker_registry[instance](
            name=name,
            config=self.config[instance],
            log_queue=self._log_queue,
            queues=queues,
            values=values,
        )
        self.subprocesses[name] = self.worker2subprocess(
            self.worker_instances[name],
            loop_flag=loop_flag,
            *args,
            **kwargs
        )
        self.subprocesses[name].start()
    
    def start(self):
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
        time.sleep(0.1)
        self._log_process.stop()