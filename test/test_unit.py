import os
import pytest
import multiprocessing as mp

import pymapp
import pymapp.shared_memory

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