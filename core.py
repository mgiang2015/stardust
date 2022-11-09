from enum import Enum
from cache import Cache
from tracker import CoreTracker

class Instruction(Enum):
    LOAD = 0
    STORE = 1
    OTHERS = 2

class Core:
    def __init__(self, id, cache: Cache, tracker: CoreTracker) -> None:
        self.cache = cache
        self.tracker = tracker
        self.id = id

    def trace(self, data) -> None:
        for label, value in data:            
            if label == Instruction.LOAD.value:
                self.handle_load(value)
            elif label == Instruction.STORE.value:
                self.handle_store(value)
            elif label == Instruction.OTHERS.value:
                self.handle_others(value)
            else:
                self.log("Invalid operation!")

    def handle_load(self, address) -> None:
        self.log(f'Handling load at address {address}')
        
        # Cache will determine whether it is a hit
        hit = True

        # Track
        self.tracker.track_load(hit=hit)

    def handle_store(self, address) -> None:
        self.log(f'Handling store at address {address}')

        # Cache will determine whether it is a hit
        hit = True

        # track
        self.tracker.track_store(hit=hit)

    def handle_others(self, cycles) -> None:
        self.log(f'Handling other operation. Takes {cycles} cycles')
        
        # parse cycles from hex to decimal
        self.tracker.track_compute(cycles=int(cycles, 16))

    def log(self, message) -> None:
        print(f'CORE {self.id}: {message}')

    def print_stats(self) -> None:
        print(f'##### STATS FOR CORE {self.id} #####')
        print(f'Overall Execution Cycles: {self.tracker.overall_cycles}')
        print(f'Compute Cycles: {self.tracker.compute_cycles}')
        print(f'Idle cycles: {self.tracker.idle_cycles}')
        print(f'Number of load operations: {self.tracker.num_load}')
        print(f'Number of store operations: {self.tracker.num_store}')
        print(f'Number of cache misses: {self.tracker.num_miss}')
        print(f'Number of accesses to private data: {self.tracker.num_private_access}')
        print(f'Number of accesses to shared data: {self.tracker.num_shared_access}')