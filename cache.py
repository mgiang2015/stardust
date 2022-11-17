from enums import BlockState, MemOperation, BlockSource
from tracker import CoreTracker

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
        ##################### Invalidation-based protocol
        if op == MemOperation.PR_INVALIDATE_LOAD:
            if self.state == BlockState.INVALID and source == BlockSource.MEMORY:
                return BlockState.EXCLUSIVE
            elif self.state == BlockState.INVALID and source == BlockSource.REMOTE_CACHE:
                return BlockState.SHARED
            else:
                return self.state
        elif op == MemOperation.PR_INVALIDATE_STORE:
            return BlockState.MODIFIED
        elif op == MemOperation.BUS_INVALIDATE_LOAD:
            if self.state == BlockState.EXCLUSIVE or self.state == BlockState.MODIFIED:
                return BlockState.SHARED
            else:
                return self.state
        elif op == MemOperation.BUS_LOAD_EXCLUSIVE:
            return BlockState.INVALID
        ##################### Update-based protocol
        elif op == MemOperation.PR_LOAD_MISS:
            if self.state == BlockState.INVALID and source == BlockSource.MEMORY:
                return BlockState.EXCLUSIVE
            elif self.state == BlockState.INVALID and source == BlockSource.REMOTE_CACHE:
                return BlockState.SHARED_CLEAN
            else:
                return self.state
        elif op == MemOperation.PR_STORE_MISS:
            if source == BlockSource.MEMORY:
                return BlockState.MODIFIED
            elif source == BlockSource.REMOTE_CACHE:
                return BlockState.SHARED_MODIFIED
            else:
                return self.state
        elif op == MemOperation.PR_UPDATE_STORE:
            if self.state == BlockState.EXCLUSIVE:
                return BlockState.MODIFIED
            elif self.state == BlockState.SHARED_CLEAN:
                return BlockState.SHARED_MODIFIED       # Achieve ownership
            else:
                return self.state
        elif op == MemOperation.BUS_UPDATE_LOAD:
            if self.state == BlockState.EXCLUSIVE:
                return BlockState.SHARED_CLEAN
            elif self.state == BlockState.MODIFIED:
                return BlockState.MODIFIED
            else:
                return self.state
        elif op == MemOperation.BUS_UPDATE_UPDATE:
            if self.state == BlockState.SHARED_MODIFIED:
                return BlockState.SHARED_CLEAN          # Give up ownership
            else:
                return self.state
        else: # More to come
            return self.state

"""
Cache: Represents an L1 Cache
- Cache has {size / block_size} cache blocks. They are divided into { associativity } sets of {size / block_sizse / associativity} blocks
- Cache should use LRU protocol
"""
class Cache:
    def __init__(self, id: int, cache_config: CacheConfig, tracker: CoreTracker) -> None:
        self.config = cache_config
        self.id = id
        self.tracker = tracker

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
            # Track hit and access
            self.tracker.track_hit()
            self.tracker.incr_data_access(state=self.blocks[cache_index][hit_block].state)
            return self.blocks[cache_index][hit_block].state

        self.tracker.incr_miss()
        self.num_operation = self.num_operation + 1
        return BlockState.INVALID

    """
    processor_store: store instruction issued by processor
        If hit: report hit to processor. Use state machine to change state accordingly.
        If miss: Handle LRU accordingly. Report miss to processor.
        Set block's last used to num_operation. num_operation++
    """
    def processor_invalidate_store(self, tag, cache_index, offset):
        hit_block = self.find_block(tag, cache_index)
        if hit_block != -1: # Hit!
            target_block = self.blocks[cache_index][hit_block]
            target_block.last_used = self.num_operation
            self.num_operation = self.num_operation + 1

            # Store old state to return (shared, modified, exclusive)
            old_state = target_block.state
            
            # hit store logic
            target_block.state = target_block.get_next_state(op=MemOperation.PR_INVALIDATE_STORE, source=BlockSource.LOCAL_CACHE)

            # Track hit
            self.tracker.track_hit()
            self.tracker.incr_data_access(old_state)
            return old_state

        self.tracker.incr_miss()
        self.num_operation = self.num_operation + 1
        return BlockState.INVALID
    
    def processor_update_store(self, tag, cache_index, offset):
        hit_block = self.find_block(tag, cache_index)
        if hit_block != -1: # Hit!
            target_block = self.blocks[cache_index][hit_block]
            target_block.last_used = self.num_operation
            self.num_operation = self.num_operation + 1

            # Store old state to return (exclusive, shared_clean, shared_modified, dirty)
            old_state = target_block.state
            
            # hit store logic
            target_block.state = target_block.get_next_state(op=MemOperation.PR_UPDATE_STORE, source=BlockSource.LOCAL_CACHE)

            # Track hit
            self.tracker.track_hit()
            self.tracker.incr_data_access(old_state)
            return old_state

        self.tracker.incr_miss()
        self.num_operation = self.num_operation + 1
        return BlockState.INVALID

    """
    pr_read_miss: bus_load but a different new state
    """
    def bus_update_load(self, tag, cache_index, offset):
        block_index = self.find_block(tag, cache_index)
        if block_index == -1:
            return False
        
        block = self.blocks[cache_index][block_index]
        self.tracker.incr_data_access(block.state)
        block.state = block.get_next_state(op=MemOperation.BUS_UPDATE_LOAD, source=BlockSource.REMOTE_CACHE)
        block.last_used = self.num_operation
        

        self.num_operation += 1
        return True

    """
    bus_load: Another remote cache is asking to read a block that you might have
        If you have it: return True. Use state machine to change state accordingly.
        If you don't: return False. No state change
    """
    def bus_invalidate_load(self, tag, cache_index, offset):
        # self.log(f'Handling bus load at tag {tag}, index {cache_index} and offset {offset}')
        block_index = self.find_block(tag, cache_index)
        if block_index == -1:
            return False
        
        block = self.blocks[cache_index][block_index]
        self.tracker.incr_data_access(block.state)
        block.state = block.get_next_state(op=MemOperation.BUS_INVALIDATE_LOAD, source=BlockSource.REMOTE_CACHE)
        block.last_used = self.num_operation

        self.num_operation += 1
        return True

    def bus_invalidate_load_exclusive(self, tag, cache_index, offset):
        # self.log(f'Handling bus load exclusive at tag {tag}, index {cache_index} and offset {offset}')
        block_index = self.find_block(tag, cache_index)
        if block_index == -1:
            return False
        
        block = self.blocks[cache_index][block_index]

        # self.tracker.incr_data_access(block.state) # Invalidation not counted as access
        block.last_used = self.num_operation
        block.state = block.get_next_state(op=MemOperation.BUS_LOAD_EXCLUSIVE, source=BlockSource.REMOTE_CACHE)

        self.num_operation += 1
        return True

    def bus_update(self, tag, cache_index, offset):
        pass

    def flush(self, tag, cache_index, offset, wrote_back):
        block_index = self.find_block(tag, cache_index)
        if block_index == -1:
            return False
        
        block = self.blocks[cache_index][block_index]
        if (block.state == BlockState.MODIFIED or block.state == BlockState.SHARED) and not wrote_back: # block is written back to memory as it is invalidated. Has to.
            self.tracker.track_evict()
        
        block.state = BlockState.INVALID
        block.last_used = self.num_operation
        return not wrote_back

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
            self.tracker.track_evict()
            target_blk.state = BlockState.INVALID
        
        # Load block into cache
        target_blk.tag = tag
        target_blk.last_used = self.num_operation

        # Set new state
        target_blk.state = target_blk.get_next_state(op=op, source=source)
        self.num_operation = self.num_operation + 1

        # Track stall time
        if source == BlockSource.REMOTE_CACHE:
            self.tracker.track_load_words_from_remote_cache(words=int(self.config.block_size / self.config.word_size))
        elif source == BlockSource.MEMORY:
            self.tracker.track_load_from_mem()

    def receive_word_from_bus(self, source: BlockSource, op: MemOperation, tag, cache_index, offset):
        blk_index = self.find_block(tag=tag, cache_index=cache_index)
        if blk_index == -1:
            return
        
        target_blk = self.blocks[cache_index][blk_index]
        
        # Set last_used
        target_blk.last_used = self.num_operation

        # Set new state
        target_blk.state = target_blk.get_next_state(op=op, source=source)
        self.num_operation = self.num_operation + 1

        # Track stall time
        self.tracker.track_load_words_from_remote_cache(words=1)


    def log(self, message: str):
        print(f'CACHE {self.id}: {message}')