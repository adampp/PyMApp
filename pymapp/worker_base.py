import logging
import logging.handlers
import multiprocessing as mp

from .constants import *

class WorkerBase():
    def __init__(
            self,
            name: str,
            config: dict,
            log_queue: mp.Queue,
            queues: dict,
            values: dict,
            ):
        self.name = name
        self.config = config
        self._log_queue = log_queue
        self.queues = queues
        self.values = values

    def _setup_log(self):
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(logging.DEBUG)
        queue_handler = logging.handlers.QueueHandler(self._log_queue)
        root_logger.addHandler(queue_handler)
        logging.info(f"Logger for {self.name} initialized")
    
    def _stop_log(self):
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)
            handler.flush()
            handler.close()
        root_logger.handlers.clear()

    def _worker_start(
            self,
            subprocess_events: dict[int, EventType],
            *args,
            **kwargs,
    ):
        self._setup_log()
        self._registered_start(subprocess_events, *args, **kwargs)

    def _worker_stop(
            self,
            subprocess_events: dict[int, EventType],
            *args,
            **kwargs,
    ):
        self._registered_stop(subprocess_events, *args, **kwargs)
        self._stop_log()

    def _worker_run(
            self,
            subprocess_events: dict[int, EventType],
            *args,
            **kwargs,
    ):
        self._registered_run(subprocess_events, *args, **kwargs)
    
    def _pass(
            self,
            subprocess_events: dict[int, EventType],
            *args,
            **kwargs,
    ):
        pass
