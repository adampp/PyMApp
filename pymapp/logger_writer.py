import os
import sys
import glob
import logging
import logging.handlers
import threading
from queue import Empty
from multiprocessing import Queue

from .constants import *
from .worker_base import WorkerBase

LOGGER_LEVEL = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

class LoggerWriter(WorkerBase):
    def __init__(self, log_queue, config):
        super().__init__("log", config, log_queue, Queue())

        if self.config["clear_all_logs_on_startup"]:
            files = glob.glob(os.path.join(self.config["directory"], "*.log"))
            for file in files:
                os.remove(file)
    
    def run(self,
            subprocess_events: dict[int, EventType],
            *args,
            **kwargs,
    ):
        try:
            msg = self._log_queue.get(timeout=self.config["queue_timeout_seconds"])
        except Empty:
            return
        
        file_logger = logging.getLogger("writer")
        if len(file_logger.handlers) < 1:
            os.makedirs(self.config["directory"], exist_ok=True)
            rotating_file_handler = logging.handlers.RotatingFileHandler(
                os.path.join(self.config["directory"], self.config["filename"]),
                maxBytes=self.config["max_bytes"],
                backupCount=self.config["backup_count"],
            )
            formatter = logging.Formatter(
                "%(asctime)s : %(levelname)s : [%(filename)s.%(funcName)s.%(lineno)d] : %(message)s"
            )
            rotating_file_handler.setFormatter(formatter)
            rotating_file_handler.setLevel(LOGGER_LEVEL[self.config["filter_level"]])
            file_logger.addHandler(rotating_file_handler)

            if self.config["use_stdout"]:
                stdout_handler = logging.StreamHandler(sys.stdout)
                stdout_handler.setFormatter(formatter)
                stdout_handler.setLevel(LOGGER_LEVEL[self.config["filter_level"]])
                file_logger.addHandler(stdout_handler)
        
        file_logger.handle(msg)