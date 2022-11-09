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
        self.processors = []
        for i in range(0, processor_num):
            self.processors.append(Core(Cache(cache_config=cache_config), CoreTracker()))

    def get_protocol(self) -> str:
        return self.protocol

    def get_cache(self) -> Cache:
        return self.cache