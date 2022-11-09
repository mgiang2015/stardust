class CoreTracker:
    def __init__(self) -> None:
        self.overall_cycles = 0         # Overall Execution Cycles (total execution time basically)
        self.compute_cycles = 0         # Number of compute cycles (number of cycles spent processing non-load/store instructions)
        self.idle_cycles = 0            # Number of cycles core spent stalling
        self.num_load = 0               # Number of load instructions
        self.num_store = 0              # Number of store instructions
        self.num_miss = 0               # Number of cache misses (for calculating miss rate)
        self.num_private_access = 0     # Number of accesses to private data (eg access line while in modified state)
        self.num_shared_access = 0      # Number of accesses to shared data (eg access line while in shared state)

    def track_compute(self, cycles: int):
        self.overall_cycles += cycles
        self.compute_cycles += cycles

    def track_stall(self, cycles: int):
        self.overall_cycles += cycles
        self.compute_cycles += cycles

    # Implement private / shared access as well
    def track_load(self, hit: bool):
        self.num_load += 1
        if hit:
            self.overall_cycles += 1
        else:
            # Miss: core stalls for 101 cycles
            self.track_stall(cycles=101)
            self.num_miss += 1

    def track_store(self, hit: bool):
        self.num_store += 1
        if hit:
            self.overall_cycles += 1
        else:
            # Miss: core stalls for 101 cycles
            self.track_stall(cycles=101)
            self.num_miss += 1

class BusTracker:
    def __init__(self) -> None:
        self.data_traffic = 0           # Amount of data traffic in bytes
        self.num_invalidation = 0       # Number of invalidations on the bus
        self.num_update = 0             # Number of updates on the bus