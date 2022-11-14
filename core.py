from bus import Bus
from cache import Cache
from tracker import CoreTracker
from enums import Instruction, BlockSource, BlockState
import math

class Core:
    def __init__(self, id, cache: Cache, bus: Bus, tracker: CoreTracker) -> None:
        self.bus = bus
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

    def process_address(self, address: str):
        # Convert address to int
        address = int(address, 16)

        num_block_entry = int(self.cache.config.block_size / self.cache.config.word_size)                   # 8
        num_set = int(self.cache.config.size / self.cache.config.block_size / self.cache.config.associativity)    # 64

        offset = address % (num_block_entry)
        cache_index = int(address / num_block_entry) % num_set
        tag = int(address / (2 ** (math.sqrt(num_block_entry) + math.sqrt(num_set))))

        return tag, cache_index, offset
    
    """
    handle_load(self, address): Processor issues a PrRd on its own L1 cache.
    If hit: Do nothing
    If PrRd is a miss: issue BusRd command to core 1 on shared bus
    End: update tracker
    """
    def handle_load(self, address) -> None:
        tag, cache_index, offset = self.process_address(address=address)
        source = BlockSource.LOCAL_CACHE
        state = self.cache.processor_load(tag=tag, cache_index=cache_index, offset=offset)
        if state != BlockState.INVALID:
            self.log("Processor load hit!")
        else:
            self.log("Processor load missed!")
            source = self.bus.load_request(id=self.id, tag=tag, cache_index=cache_index, offset=offset)

        # Use source to keep track of cycles. should always be
        self.tracker.track_load(source, int(self.cache.config.block_size / self.cache.config.word_size))
    
    """
    handle_store(self, address): Processor issues a PrWr on its own L1 cache.
    If hit: Issue bus command to invalidate everything else (flush?). DRAGON: update?
    If miss: issue BusRdX command to get exclusive access to 1 block
    """
    def handle_store(self, address) -> None:
        # self.log(f'Handling store at address {address}')
        pass

    """
    handle_others(self, cycles): Basically increases overall execution cycle and compute cycle
    """
    def handle_others(self, cycles) -> None:
        # self.log(f'Handling other operation. Takes {cycles} cycles')
        
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