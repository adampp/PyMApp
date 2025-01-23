import time
import logging

import pymapp

@pymapp.register()
class SleepyWorker(pymapp.WorkerBase):
    def __init__(self, name, config, log_queue, queues, values):
        super().__init__(name, config, log_queue, queues, values)
        self.i = 0

    def start(
            self,
            subprocess_events: dict[int, pymapp.EventType],
            *args,
            **kwargs,
    ):
        logging.info('start!')

    def run(
            self,
            subprocess_events: dict[int, pymapp.EventType],
            *args,
            **kwargs,
    ):
        logging.info(f"sleep count = {self.i}")
        time.sleep(1)

    def stop(
            self,
            subprocess_events: dict[int, pymapp.EventType],
            *args,
            **kwargs,
    ):
        logging.info('stop!')