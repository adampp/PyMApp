import os
import time
import pymapp
import logging

import sleepy_worker

CONFIG_LOCATION = os.path.dirname(__file__)

@pymapp.register_mapp_class(os.path.join(CONFIG_LOCATION, "config.json"))
class MyTestApplication(pymapp.MApp):
    def __init__(self):
        self.a = 1
        self.b = 2

    @pymapp.register_setup_method()
    def setup(self):
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
    
    @pymapp.register_main_method()
    def main(self):
        print('a')


if __name__ == "__main__":
    my_test = MyTestApplication()
    my_test.start()
    time.sleep(3)
    pymapp.send_message('sleepy1', "Hey sleepy1, I'm from main!")
    time.sleep(2)
    pymapp.send_message('sleepy2', "Hey sleepy2, I'm from main!")
    time.sleep(2)
    my_test.stop()