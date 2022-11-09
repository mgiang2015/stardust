import threading
from enum import Enum
from cache import Cache, CacheConfig
from core import Core
from tracker import CoreTracker, BusTracker
from bus import Bus

class Protocol(Enum):
    MESI = 0
    DRAGON = 1
    NONE = 2

# shared memory class
class Memory:
    pass

# 1 protocol, 1 shared memory, 1 shared bus, 4 processors with 1 L1 cache each
class System:
    def __init__(self, protocol: Protocol, processor_num: int, cache_config: CacheConfig) -> None:
        self.protocol = protocol
        self.memory = Memory()
        self.bus = Bus(BusTracker())
        self.cores = []
        for i in range(0, processor_num):
            self.cores.append(Core(id=i, cache=Cache(cache_config=cache_config), tracker=CoreTracker()))
        
        self.threads = []

    def get_protocol(self) -> str:
        return self.protocol

    def get_cache(self) -> Cache:
        return self.cache

    def add_thread(self, data, core_id) -> None:
        t = threading.Thread(target=self.cores[core_id].trace, args=(data,))
        self.threads.append(t)

    def trace(self):
        for thread in self.threads:
            thread.start()