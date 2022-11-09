from enum import Enum
from cache import Cache, CacheConfig

class Protocol(Enum):
    MESI = 0
    DRAGON = 1
    NONE = 2


# shared memory class
class Memory:
    pass

# shared bus class
class Bus:
    pass

class Core:
    def __init__(self, cache) -> None:
        self.cache = cache

# 1 protocol, 1 shared memory, 1 shared bus, 4 processors with 1 L1 cache each
class System:
    def __init__(self, protocol: Protocol, processor_num: int, cache_config: CacheConfig) -> None:
        self.protocol = protocol
        self.memory = Memory()
        self.bus = Bus()
        self.processors = []
        for i in range(0, processor_num):
            self.processors.append(Core(Cache(cache_config=cache_config)))

    def get_protocol(self) -> str:
        return self.protocol

    def get_cache(self) -> Cache:
        return self.cache