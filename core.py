from bus import Bus
from cache import Cache
from tracker import CoreTracker
from enums import Instruction, BlockSource, BlockState, Protocol
import math

class Core:
    def __init__(self, id, cache: Cache, bus: Bus, tracker: CoreTracker, protocol: Protocol) -> None:
        self.protocol = protocol
        self.bus = bus
        self.cache = cache
        self.tracker = tracker
        self.id = id

    def trace(self, data) -> None:
        for label, value in data:
            if self.protocol == Protocol.MESI:
                if label == Instruction.LOAD.value:
                    self.handle_invalidate_load(value)
                elif label == Instruction.STORE.value:
                    self.handle_invalidation_store(value)
                elif label == Instruction.OTHERS.value:
                    self.handle_others(value)
                else:
                    self.log("Invalid operation!")
            elif self.protocol == Protocol.DRAGON:
                if label == Instruction.LOAD.value:
                    self.handle_update_load(value)
                elif label == Instruction.STORE.value:
                    self.handle_update_store(value)
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
    handle_invalidate_load(self, address): Processor issues a PrRd on its own L1 cache.
    If hit: Do nothing
    If PrRd is a miss: issue BusRd command to core 1 on shared bus
    End: update tracker
    """
    def handle_invalidate_load(self, address) -> None:
        tag, cache_index, offset = self.process_address(address=address)
        source = BlockSource.LOCAL_CACHE
        state = self.cache.processor_load(tag=tag, cache_index=cache_index, offset=offset)
        if state != BlockState.INVALID:
            self.log(f"Processor load hit! Tag {tag} index {cache_index}")
        else:
            self.log(f"Processor load missed! Tag {tag} index {cache_index}")
            source = self.bus.bus_load_request(id=self.id, tag=tag, cache_index=cache_index, offset=offset)

        # Use source to keep track of cycles. should always be
        self.tracker.track_load(source, int(self.cache.config.block_size / self.cache.config.word_size))

    """
    handle_invalidation_store(self, address): Processor issues a PrWr on its own L1 cache.
    If hit: Issue bus command to invalidate or update everything else DEPENDING ON PROTOCOL
    If miss: issue BusRdX command to get exclusive access to 1 block
    """
    def handle_invalidation_store(self, address) -> None:
        tag, cache_index, offset = self.process_address(address=address)
        source = BlockSource.LOCAL_CACHE
        state = self.cache.processor_invalidate_store(tag=tag, cache_index=cache_index, offset=offset)
        # hit but exclusive / modified: ignore
        if state == BlockState.SHARED: # hit and shared
            self.log(f"Processor store hit! Tag {tag} index {cache_index}")
            self.bus.flush_request(id=self.id, tag=tag, cache_index=cache_index, offset=offset)
        elif state == BlockState.INVALID: # miss
            self.log(f"Processor store miss! Tag {tag} index {cache_index}")
            source = self.bus.bus_load_exclusive_request(id=self.id, tag=tag, cache_index=cache_index, offset=offset)
            self.cache.processor_invalidate_store(tag=tag, cache_index=cache_index, offset=offset)

        self.tracker.track_store(source=source, words=int(self.cache.config.block_size / self.cache.config.word_size))

    """
    def handle_update_load(self, address): Same as invalidate load, but calls a different bus request
    """
    def handle_update_load(self, address) -> None:
        tag, cache_index, offset = self.process_address(address=address)
        source = BlockSource.LOCAL_CACHE
        state = self.cache.processor_load(tag=tag, cache_index=cache_index, offset=offset)
        if state != BlockState.INVALID:
            self.log(f"Processor load hit! Tag {tag} index {cache_index}")
        else:
            self.log(f"Processor load missed! Tag {tag} index {cache_index}")
            source = self.bus.pr_load_miss_request(id=self.id, tag=tag, cache_index=cache_index, offset=offset)

        # Use source to keep track of cycles. should always be
        self.tracker.track_load(source, int(self.cache.config.block_size / self.cache.config.word_size))

    """
    handle_update_store(self, address): Update-based store. Issues a PrWr on its own L1 cache.
    """
    def handle_update_store(self, address) -> None:
        tag, cache_index, offset = self.process_address(address=address)
        source = BlockSource.LOCAL_CACHE
        state = self.cache.processor_update_store(tag=tag, cache_index=cache_index, offset=offset)
        # Ignore EXCLUSIVE, MODIFIED
        if state == BlockState.INVALID: # miss
            self.log(f"Processor store miss! Tag {tag} index {cache_index}")
            source = self.bus.pr_store_miss_request(id=self.id, tag=tag, cache_index=cache_index, offset=offset)
            # Request bus for ownership if not loaded from memory by calling update
            if source == BlockSource.REMOTE_CACHE:
                self.cache.processor_update_store(id=self.id, tag=tag, cache_index=cache_index, offset=offset)  # Write
                self.bus.bus_update_request(id=self.id, tag=tag, cache_index=cache_index, offset=offset)        # Claim ownership and update the rest
        elif state == BlockState.SHARED_CLEAN: # Get ownership of block. Must request on bus
            self.cache.processor_update_store(id=self.id, tag=tag, cache_index=cache_index, offset=offset)      # Write
            self.bus.bus_update_request(id=self.id, tag=tag, cache_index=cache_index, offset=offset)            # Claim ownership and update the rest
        elif state == BlockState.SHARED_MODIFIED: # Already has ownership of block. Request update all others.
            self.bus.bus_update_request(id=self.id, tag=tag, cache_index=cache_index, offset=offset)
        
        self.tracker.track_store(source=source, words=int(self.cache.config.block_size / self.cache.config.word_size))
       
    """
    handle_others(self, cycles): Basically increases overall execution cycle and compute cycle
    """
    def handle_others(self, cycles) -> None:        
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