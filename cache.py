from enum import Enum
import math
"""
CacheConfig: structure for cache configuration
"""
class CacheConfig:
    def __init__(self, size: int, associativity: int, block_size: int, word_size: int) -> None:
        self.size = size
        self.associativity = associativity
        self.block_size = block_size
        self.word_size = word_size

"""
CacheBlock: Represents a cache block with size {block_size} and has {block_size / word_size} entries
- Each cache block has a state (MESI)
- Each block keeps track of whether it is least recently used (lru)
"""
class CacheBlock:
    def __init__(self, block_size: int, word_size: int) -> None:
        self.state = BlockState.INVALID     # We can consider INVALID as not occupied
        self.last_used = 0                  # Gets updated for every load/store operation. For LRU implementation
        self.tag = 0                        # Address tag

        entry_num = int(block_size / word_size)  # default: 32 / 4 = 8
        self.entries = []
        for i in range(0, entry_num):
            self.entries.append(0)
    
    def is_invalid(self):
        return self.state == BlockState.INVALID

    def is_shared(self):
        return self.state == BlockState.SHARED
    
    def is_private(self):
        return self.state == BlockState.EXCLUSIVE or self.state == BlockState.MODIFIED

    def set_last_used(self, new_last_used: int):
        self.last_used = new_last_used

"""
Cache: Represents an L1 Cache
- Cache has {size / block_size} cache blocks. They are divided into { associativity } sets of {size / block_sizse / associativity} blocks
- Cache should use LRU protocol
"""
class Cache:
    def __init__(self, cache_config: CacheConfig) -> None:
        self.config = cache_config
        
        self.blocks = []
        num_sets = int(self.config.size / self.config.block_size / self.config.associativity)
        for set in range(0, num_sets):
            # 64 sets of 2 cache blocks
            self.blocks.append([])
            for _ in range(0, self.config.associativity):
                self.blocks[set].append(CacheBlock(self.config.block_size, self.config.word_size))

        # For LRU implementation. Each cache block receives a new last_used each load/store
        self.operation_num = 0

    def process_address(self, address: str):
        # Convert address to int
        address = int(address, 16)

        num_block_entry = int(self.config.block_size / self.config.word_size)                   # 8
        num_set = int(self.config.size / self.config.block_size / self.config.associativity)    # 64

        offset = address % (num_block_entry)
        cache_index = (address >> math.sqrt(num_block_entry)) % num_set
        tag = address >> (math.sqrt(num_block_entry) + math.sqrt(num_set))

        return tag, cache_index, offset

    def load_address(self, address: str):
        # Implement MESI n DRAGON here
        pass
    
    def store_address(self, address: str):
        # Implement MESI and DRAGON here
        pass

class BlockState(Enum):
    MODIFIED = 0
    EXCLUSIVE = 1
    SHARED = 2
    INVALID = 3