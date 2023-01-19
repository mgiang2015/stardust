import threading
from enums import Protocol
from cache import Cache, CacheConfig
from core import Core
from tracker import CoreTracker, BusTracker
from bus import Bus
from threading import Lock
import sys

# 1 protocol, 1 shared bus, 4 processors with 1 L1 cache each
class System:
    def __init__(self, protocol: Protocol, processor_num: int, cache_config: CacheConfig, filename: str) -> None:
        self.protocol = protocol
        self.bus = Bus(BusTracker(), cache_config=cache_config, lock=Lock())
        self.cores = []
        self.filename = filename
        for i in range(0, processor_num):
            shared_tracker = CoreTracker()
            new_cache = Cache(id=i, cache_config=cache_config, tracker=shared_tracker)
            # Both bus and core has access to given cache
            self.cores.append(Core(id=i, bus=self.bus, cache=new_cache, tracker=shared_tracker, protocol=protocol))
            self.bus.add_cache(new_cache)
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

        # Wait for all threads to finish
        for thread in self.threads:
            thread.join()

        print("\n\n**STATISTICS**\n\n")
        
        # Direct this to a file instead of stdout
        with open(self.filename, 'w+') as sys.stdout:
            for core in self.cores:
                core.print_stats()

            self.bus.print_stats()