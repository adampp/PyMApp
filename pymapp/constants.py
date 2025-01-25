import enum
from multiprocessing.synchronize import Event as EventType
from multiprocessing.synchronize import Lock as LockType

# Event Dictionary keys
class EventDictKeys(enum.Enum):
    SYNC_STOP = 1
    DONT_KILL = 2
    HEARTBEAT = 3
    CONTINUE = 4