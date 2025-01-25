import copy
import pickle
import platform
from multiprocessing.shared_memory import SharedMemory

from .constants import *

class PyMAppSharedMemory():
    def __init__(self, name: str, size: int, create: bool, mutex: LockType):
        mutex.acquire()
        self._size = size
        temp_size = bytearray(size).__sizeof__()

        self._shared_mem = SharedMemory(name=name, create=create, size=temp_size)
        self._actual_size = len(self._shared_mem.buf)
        self._mutex = mutex
        mutex.release()

    def write(self, data: object) -> None:
        data_bytes = pickle.dumps(data)
        n_bytes = len(data_bytes)
        if n_bytes > self._actual_size:
            raise BufferError(f"Unable to write {n_bytes} bytes to a buffer of size {self._actual_size}")
        
        self._mutex.acquire()
        self._shared_mem.buf[:n_bytes] = data_bytes
        self._mutex.release()

    def read(self) -> object:
        self._mutex.acquire()
        copied_data = copy.deepcopy(bytearray(self._shared_mem.buf))
        self._mutex.release()

        if platform.system() == "Windows":
            empty_array = True
            for byte in copied_data:
                if byte != 0:
                    empty_array = False
                    break
            if empty_array:
                return None
        else:
            if copied_data == bytearray(self._actual_size):
                return None
        
        return pickle.loads(copied_data)
    
    def close(self) -> None:
        self._shared_mem.close()

    def unlink(self) -> None:
        self._shared_mem.close()
        self._shared_mem.unlink()