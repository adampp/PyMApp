import os
import time
import pymapp
import logging

import sleepy_worker

CONFIG_LOCATION = os.path.dirname(__file__)

class MyTestApplication(pymapp.MApp):
    def __init__(self):
        super().__init__(os.path.join(CONFIG_LOCATION, "config.json"))

        self.create_subprocess(
            name="sleepy1",
            instance="SleepyWorker",
            loop_flag=True,
            start_i=10
        )
        self.create_subprocess(
            name="sleepy2",
            instance="SleepyWorker",
            loop_flag=True,
            start_i=2,
        )

        self.add_shared_memory(
            "test",
            1_000,
            ["sleepy1", "sleepy2"]
        )
    
    def run(self):
        self.start()
        time.sleep(5)


if __name__ == "__main__":
    my_test = MyTestApplication()
    my_test.run()