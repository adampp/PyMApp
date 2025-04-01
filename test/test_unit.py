import os
import time
import pytest
import platform
import multiprocessing as mp

import pymapp
import pymapp.shared_memory
from platform import python_version

@pytest.fixture
def get_mapp_class():
    import sleepy_worker
    from application import MyTestApplication
    
    test_app = MyTestApplication()
    test_app._setup()
    yield test_app

    test_app.stop()

@pytest.fixture
def get_worker(get_mapp_class: pymapp.MApp):
    yield get_mapp_class._worker_instances["sleepy1"]

def mem_addr(x):
    return hex(int(object.__repr__(x).partition('object at ')[2].strip('>'), 16))

def test_worker_decorator(get_worker:pymapp.WorkerBase):
    assert get_worker.name == "sleepy1"
    assert "test_key" in get_worker.config
    assert get_worker.config["test_key"] == "test_value"
    assert isinstance(get_worker._log_queue, mp.queues.Queue)
    assert isinstance(get_worker._message_queue, mp.queues.Queue)
    assert isinstance(get_worker._sender_queues, dict)
    assert "sleepy1" in get_worker._sender_queues
    assert "sleepy2" in get_worker._sender_queues
    assert isinstance(get_worker._sender_queues["sleepy1"], mp.queues.Queue)
    assert isinstance(get_worker._sender_queues["sleepy2"], mp.queues.Queue)
    assert "test" in get_worker.shared_memory
    assert isinstance(get_worker.shared_memory["test"], pymapp.shared_memory.PyMAppSharedMemory)

    assert callable(get_worker.add_shared_memory)
    assert callable(get_worker._setup_log)
    assert callable(get_worker._stop_log)
    assert callable(get_worker._registered_start)
    assert callable(get_worker._registered_stop)
    assert callable(get_worker._registered_run)
    assert callable(get_worker._registered_message_handler)
    assert callable(get_worker._worker_start)
    assert callable(get_worker._worker_stop)
    assert callable(get_worker._worker_run)

    assert "SleepyWorker" in pymapp.registry._registry.workers

    from sleepy_worker import SleepyWorker
    assert pymapp.registry._registry.workers["SleepyWorker"] is SleepyWorker
    del SleepyWorker
    
def test_register_start(get_worker:pymapp.WorkerBase):
    from sleepy_worker import SleepyWorker
    registry = pymapp.registry._registry
    assert SleepyWorker.start is registry.worker_start_methods["SleepyWorker"]
    assert SleepyWorker.start is get_worker._registered_start.__func__
    del SleepyWorker
    
def test_register_run(get_worker:pymapp.WorkerBase):
    from sleepy_worker import SleepyWorker
    registry = pymapp.registry._registry
    assert SleepyWorker.run is registry.worker_run_methods["SleepyWorker"]
    assert SleepyWorker.run is get_worker._registered_run.__func__
    del SleepyWorker
    
def test_register_stop(get_worker:pymapp.WorkerBase):
    from sleepy_worker import SleepyWorker
    registry = pymapp.registry._registry
    assert SleepyWorker.stop is registry.worker_stop_methods["SleepyWorker"]
    assert SleepyWorker.stop is get_worker._registered_stop.__func__
    del SleepyWorker

def test_register_message_handler(get_worker:pymapp.WorkerBase):
    from sleepy_worker import SleepyWorker
    registry = pymapp.registry._registry
    assert SleepyWorker.message_handler is registry.worker_message_handler_methods["SleepyWorker"]
    assert SleepyWorker.message_handler is get_worker._registered_message_handler.__func__
    del SleepyWorker

def test_register_main(get_mapp_class:pymapp.MApp):
    from application import MyTestApplication
    registry = pymapp.registry._registry
    assert MyTestApplication.main is registry.main_method
    assert MyTestApplication.main is get_mapp_class._main.__func__
    del MyTestApplication

def test_register_setup(get_mapp_class:pymapp.MApp):
    from application import MyTestApplication
    registry = pymapp.registry._registry
    assert MyTestApplication.setup is registry.setup_method
    assert MyTestApplication.setup is get_mapp_class._setup.__func__
    del MyTestApplication

@pytest.mark.serial
def test_run():
    from application import MyTestApplication
    my_test = MyTestApplication()
    log_filename = f"{os.getenv("GITHUB_ACTION")}_{os.getenv("GITHUB_JOB")}_{platform.python_version()}.log"
    my_test._logger_writer.config["filename"] = log_filename
    my_test.start()
    with open(os.path.join('logs', log_filename), 'r') as fid:
        log_text = fid.read()
    
    print('\n\n\n\nBREAK BREAK')
    print(log_text)
    # assert "Starting process log" in log_text
    # assert "Started process log" in log_text
    # assert "Logger initialized" in log_text
    # assert "Starting process sleepy1" in log_text
    # assert "Started process sleepy1" in log_text
    # assert "Starting process sleepy2" in log_text
    # assert "Started process sleepy2" in log_text
    # assert "Logger for sleepy1 initialized" in log_text
    # assert "start!" in log_text
    # assert "Startup target for sleepy1 complete" in log_text
    # assert "Logger for sleepy2 initialized" in log_text
    # assert "Startup target for sleepy2 complete" in log_text
    # assert "sleepy1 count = 10 : wrote" in log_text
    # assert "sleepy2 count = 2 : hi from sleepy1! 10" in log_text
    # assert "I, sleepy2, am at 2" in log_text
    # assert "sleepy1 count = 11 : wrote" in log_text
    # assert "I, sleepy1, am at 10" in log_text
    # assert "I, sleepy1, am at 11" in log_text
    # assert "sleepy2 count = 3 : hi from sleepy1! 11" in log_text
    # assert "I, sleepy2, am at 3" in log_text
    # assert "sleepy1 count = 12 : wrote" in log_text
    # assert "I, sleepy1, am at 12" in log_text
    # assert "sleepy2 count = 4 : hi from sleepy1! 12" in log_text
    # assert "I, sleepy2, am at 4" in log_text
    # assert "sleepy1 count = 13 : wrote" in log_text
    # assert "I, sleepy1, am at 13" in log_text
    # assert "sleepy2 count = 5 : hi from sleepy1! 13" in log_text
    # assert "I, sleepy2, am at 5" in log_text
    # assert "sleepy1 count = 14 : wrote" in log_text
    # assert "I, sleepy1, am at 14" in log_text
    # assert "sleepy2 count = 6 : hi from sleepy1! 14" in log_text
    # assert "Stopping process sleepy1" in log_text
    # assert "All subprocesses alive." in log_text
    # assert "Main loop for sleepy1 complete" in log_text
    # assert "stop!" in log_text
    # assert "Stopped sleepy1" in log_text
    # assert "Stopping process sleepy2" in log_text
    # assert "Main loop for sleepy2 complete" in log_text
    # assert "Stopped sleepy2" in log_text
    # assert "Stopping process log" in log_text