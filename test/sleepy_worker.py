import time
import logging

import pymapp

@pymapp.register_worker()
class SleepyWorker(pymapp.WorkerBase):
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
        if self.name == "sleepy1":
            self.shared_memory['test'].write(f"hi from sleepy1! {self.i}")
            read_str = "wrote"
        elif self.name == "sleepy2":
            read_str = self.shared_memory['test'].read()
        logging.info(f"{self.name} count = {self.i} : {read_str}")
        time.sleep(1)
        self.i += 1
        if self.i > 10:
            time.sleep(6)

    @pymapp.stop_method()
    def stop(
            self,
            subprocess_events: dict[int, pymapp.EventType],
            *args,
            **kwargs,
    ):
        logging.info('stop!')