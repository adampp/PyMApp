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
            queues = {},
            values = {},
        )
    
    def run(self):
        self.start()
        time.sleep(5)


if __name__ == "__main__":
    my_test = MyTestApplication()
    my_test.run()