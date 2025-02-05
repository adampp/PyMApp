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
    return test_app

@pytest.fixture
def get_worker(get_mapp_class: pymapp.MApp):
    return get_mapp_class._worker_instances["sleepy1"]


def test_worker_decorator(get_worker:pymapp.WorkerBase):
    assert get_worker.name == "sleepy1"
    assert "test_key" in get_worker.config
    assert get_worker.config["test_key"] == "test_value"
    print(get_worker._log_queue)
    assert isinstance(get_worker._log_queue, mp.queues.Queue)
    assert isinstance(get_worker._message_queue, mp.queues.Queue)
    assert isinstance(get_worker._sender_queues, dict)
    assert "sleepy1" in get_worker._sender_queues
    assert "sleepy2" in get_worker._sender_queues
    assert isinstance(get_worker._sender_queues["sleepy1"], mp.queues.Queue)
    assert isinstance(get_worker._sender_queues["sleepy2"], mp.queues.Queue)
    assert "test" in get_worker.shared_memory
    print(get_worker.shared_memory["test"])
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
    print(pymapp.registry._registry.workers["SleepyWorker"])
    import sleepy_worker
    print(pymapp.registry._registry.workers["SleepyWorker"] is sleepy_worker.SleepyWorker)
    del sleepy_worker
    
