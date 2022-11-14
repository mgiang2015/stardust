from enums import BlockState, MemOperation, BlockSource

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
    Simulate cache's state machine for MESI / DRAGON
    """
    def get_next_state(self, op: MemOperation, source: BlockSource) -> BlockState:
        if op == MemOperation.PR_LOAD:
            if self.state == BlockState.INVALID and source == BlockSource.MEMORY:
                return BlockState.EXCLUSIVE
            elif self.state == BlockState.INVALID and source == BlockSource.REMOTE_CACHE:
                return BlockState.SHARED
            else:
                return self.state
        elif op == MemOperation.BUS_LOAD:
            if self.state == BlockState.EXCLUSIVE or self.state == BlockState.MODIFIED:
                return BlockState.SHARED
            else:
                return self.state
        elif op == MemOperation.BUS_LOAD_EXCLUSIVE:
            return BlockState.INVALID
        elif op == MemOperation.PR_STORE:
            return BlockState.MODIFIED
        else: # More to come
            return self.state

"""
Cache: Represents an L1 Cache
- Cache has {size / block_size} cache blocks. They are divided into { associativity } sets of {size / block_sizse / associativity} blocks
- Cache should use LRU protocol
"""
class Cache:
    def __init__(self, id: int, cache_config: CacheConfig) -> None:
        self.config = cache_config
        self.id = id
        # For LRU implementation. Each cache block receives a new last_used each load/store
        self.num_operation = 0

        self.blocks = []
        num_sets = int(self.config.size / self.config.block_size / self.config.associativity)
        for set in range(0, num_sets):
            # 64 sets of 2 cache blocks
            self.blocks.append([])
            for _ in range(0, self.config.associativity):
                self.blocks[set].append(CacheBlock(self.config.block_size, self.config.word_size))

       

    """
    A hit happens when blocks[cache_index] returns a set of blocks, in which one has tag === given tag AND that block is not invalid
    Returns index of block in the given set
    """
    def find_block(self, tag, cache_index) -> int:
        for block_id, block in enumerate(self.blocks[cache_index]):
            if block.tag == tag and not block.is_invalid():
                return block_id
        
        return -1

    """
    processor_load: load instruction issued by processor
        If hit: report hit to processor. Set block's last used to num_operation.
        If miss: Report miss to processor
        num_operation++
    """
    def processor_load(self, tag, cache_index, offset) -> BlockState:
        # self.log(f'Handling processor load at tag {tag}, index {cache_index} and offset {offset}')
        hit_block = self.find_block(tag, cache_index)
        if hit_block != -1: # Hit!
            self.blocks[cache_index][hit_block].last_used = self.num_operation
            self.num_operation = self.num_operation + 1
            return self.blocks[cache_index][hit_block].state

        self.num_operation = self.num_operation + 1
        return BlockState.INVALID

    """
    processor_store: store instruction issued by processor
        If hit: report hit to processor. Use state machine to change state accordingly.
        If miss: Handle LRU accordingly. Report miss to processor.
        Set block's last used to num_operation. num_operation++
    """
    def processor_store(self, tag, cache_index, offset):
        # self.log(f'Handling processor store at tag {tag}, index {cache_index} and offset {offset}')
        hit_block = self.find_block(tag, cache_index)
        if hit_block != -1: # Hit!
            target_block = self.blocks[cache_index][hit_block]
            target_block.last_used = self.num_operation
            self.num_operation = self.num_operation + 1

            # Store old state to return (shared, modified, exclusive)
            old_state = target_block.state
            
            # hit store logic
            target_block.state = target_block.get_next_state(op=MemOperation.PR_STORE, source=BlockSource.LOCAL_CACHE)

            return old_state

        self.num_operation = self.num_operation + 1
        return BlockState.INVALID
    
    """
    bus_load: Another remote cache is asking to read a block that you might have
        If you have it: return True. Use state machine to change state accordingly.
        If you don't: return False. No state change
    """
    def bus_load(self, tag, cache_index, offset):
        # self.log(f'Handling bus load at tag {tag}, index {cache_index} and offset {offset}')
        block_index = self.find_block(tag, cache_index)
        if block_index == -1:
            return False
        
        block = self.blocks[cache_index][block_index]
        block.state = block.get_next_state(op=MemOperation.BUS_LOAD, source=BlockSource.REMOTE_CACHE)
        block.last_used = self.num_operation

        self.num_operation += 1
        return True

    def bus_load_exclusive(self, tag, cache_index, offset):
        # self.log(f'Handling bus load exclusive at tag {tag}, index {cache_index} and offset {offset}')
        block_index = self.find_block(tag, cache_index)
        if block_index == -1:
            return False
        
        block = self.blocks[cache_index][block_index]
        block.state = block.get_next_state(op=MemOperation.BUS_LOAD_EXCLUSIVE, source=BlockSource.REMOTE_CACHE)

        self.num_operation += 1
        return True

    def bus_update(self, tag, cache_index, offset):
        pass

    """
    receive_block_from_bus: Adds new block to cache. Handle LRU if needed.
    Let cache block decide its own next state
    """
    def receive_block_from_bus(self, source: BlockSource, op: MemOperation, tag, cache_index, offset):
        target_blk = None
        # Find invalid cache block to insert itself there
        for block in self.blocks[cache_index]:
            if block.is_invalid():
                target_blk = block
                break
        
        # If no invalid blocks found, find lru block
        if target_blk == None:
            min_last_used = 2 ** 31 + (2 ** 31 - 1)
            for block in self.blocks[cache_index]:
                if block.last_used < min_last_used:
                    target_blk = block
                    min_last_used = block.last_used

            # Invalidate chosen block
            self.log(f'Evicting block with tag {target_blk.tag}')
            target_blk.state = BlockState.INVALID
        
        # Load block into cache
        target_blk.tag = tag
        target_blk.last_used = self.num_operation

        # Set new state
        target_blk.state = target_blk.get_next_state(op=op, source=source)
        self.num_operation = self.num_operation + 1

    def log(self, message: str):
        print(f'CACHE {self.id}: {message}')