import time
import logging

import pymapp

@pymapp.register()
class SleepyWorker():
    def __init__(self, start_i):
        self.i = start_i

    @pymapp.start_method()
    def start(
            self,
            subprocess_events: dict[int, pymapp.EventType],
            *args,
            **kwargs,
    ):
        logging.info('start!')

    @pymapp.run_method()
    def run(
            self,
            subprocess_events: dict[int, pymapp.EventType],
            *args,
            **kwargs,
    ):
        logging.info(f"sleep count = {self.i}")
        time.sleep(1)
        self.i += 1

    @pymapp.stop_method()
    def stop(
            self,
            subprocess_events: dict[int, pymapp.EventType],
            *args,
            **kwargs,
    ):
        logging.info('stop!')