from enums import BlockState

class CoreTracker:
    def __init__(self) -> None:
        self.overall_cycles = 0         # Overall Execution Cycles (total execution time basically)
        self.hit_cycles = 0             # Cycles incurred by cache hit
        self.compute_cycles = 0         # Number of compute cycles (number of cycles spent processing non-load/store instructions)
        self.idle_cycles = 0            # Number of cycles core spent stalling
        self.num_load = 0               # Number of load instructions
        self.num_store = 0              # Number of store instructions
        self.num_miss = 0               # Number of cache misses (for calculating miss rate)
        self.num_private_access = 0     # Number of accesses to private data (eg access line while in modified state)
        self.num_shared_access = 0      # Number of accesses to shared data (eg access line while in shared state)
    
    def track_hit_cycles(self):
        self.overall_cycles += 1
        self.hit_cycles += 1

    def track_compute(self, cycles: int):
        self.overall_cycles += cycles
        self.compute_cycles += cycles

    def track_stall(self, cycles: int):
        self.overall_cycles += cycles
        self.idle_cycles += cycles

    # Implement private / shared access as well
    # words = number of words transferred between 2 caches. Only used for REMOTE_CACHE
    def incr_load(self):
        self.num_load += 1

    def incr_store(self):
        self.num_store += 1
    
    def incr_miss(self):
        self.num_miss += 1

    def incr_shared_data_access(self):
        self.num_shared_access += 1

    def incr_private_data_access(self):
        self.num_private_access += 1
    
    def incr_data_access(self, state: BlockState):
        if state in [BlockState.SHARED, BlockState.SHARED_CLEAN, BlockState.SHARED_MODIFIED]:
            self.incr_shared_data_access()
        elif state in [BlockState.MODIFIED, BlockState.DIRTY, BlockState.EXCLUSIVE]:
            self.incr_private_data_access()

    def track_hit(self):
        self.track_hit_cycles()

    def track_evict(self):
        self.track_stall(cycles=100)

    def track_load_words_from_remote_cache(self, words: int):
        self.track_stall(cycles=2*words)
    
    def track_load_from_mem(self):
        # 1 cycle to check from cache first
        self.track_hit_cycles()
        self.track_stall(cycles=100)


class BusTracker:
    def __init__(self) -> None:
        self.data_traffic = 0           # Amount of data traffic in bytes
        self.num_invalidation = 0       # Number of invalidations on the bus
        self.num_update = 0             # Number of updates on the bus

    def track_traffic(self, word_size: int, words: int):
        self.data_traffic += word_size * words

    def track_invalidation(self, blocks: int):
        self.num_invalidation += blocks

    def track_update(self, updates: int):
        self.num_update += updates