from tracker import BusTracker
from cache import Cache, CacheConfig
from enums import BlockSource, MemOperation

# shared bus class
class Bus:
    def __init__(self, tracker: BusTracker, cache_config: CacheConfig) -> None:
        self.tracker = tracker
        self.cache_config = cache_config
        self.caches = []

    def add_cache(self, cache: Cache):
        self.caches.append(cache)

    ########## Invalidation-based bus requests
    def bus_load_request(self, id, tag, cache_index, offset) -> BlockSource:
        # self.log(f'Received load_request from core {id} with tag {tag}, index {cache_index} and offset {offset}')
        found_in_remote_cache = False
        for c in self.caches:
            # If bus finds a valid copy in one of the caches
            if c.id != id and c.bus_invalidate_load(tag, cache_index, offset):
                # deliver block from REMOTE_CACHE to current cache
                if not found_in_remote_cache:
                    self.deliver_block(source=BlockSource.REMOTE_CACHE, op=MemOperation.PR_INVALIDATE_LOAD, target_id=id, tag=tag, cache_index=cache_index, offset=offset)
                    found_in_remote_cache = True
        if found_in_remote_cache:
            return BlockSource.REMOTE_CACHE
        else:
            self.deliver_block(source=BlockSource.MEMORY, op=MemOperation.PR_INVALIDATE_LOAD, target_id=id, tag=tag, cache_index=cache_index, offset=offset)
            return BlockSource.MEMORY

    def bus_load_exclusive_request(self, id, tag, cache_index, offset):
        self.log(f'Received load_exclusive_request from core {id} with tag {tag}, index {cache_index} and offset {offset}')
        found_in_remote_cache = False
        for c in self.caches:
            # If bus finds a valid copy in one of the caches
            self.log(f'Looking at cache {c.id}')
            if c.id != id and c.bus_invalidate_load_exclusive(tag, cache_index, offset): # invalidate block immediately with bus_load_exclusive
                self.tracker.track_invalidation(blocks=1)
                self.log(f'Invalidating cache {c.id}')
                
                if not found_in_remote_cache:
                    # deliver block from REMOTE_CACHE to current cache
                    self.deliver_block(source=BlockSource.REMOTE_CACHE, op=MemOperation.PR_INVALIDATE_STORE, target_id=id, tag=tag, cache_index=cache_index, offset=offset)
                    found_in_remote_cache = True
        
        # Only going to be used for MESI and MOESI
        if found_in_remote_cache:
            return BlockSource.REMOTE_CACHE
        else:
            self.deliver_block(source=BlockSource.MEMORY, op=MemOperation.PR_INVALIDATE_STORE, target_id=id, tag=tag, cache_index=cache_index, offset=offset)
            return BlockSource.MEMORY

    ########## Update-based bus requests
    def pr_load_miss_request(self, id, tag, cache_index, offset):
        found_in_remote_cache = False
        for c in self.caches:
            # If bus finds a valid copy in one of the caches
            if c.id != id and c.bus_update_load(tag, cache_index, offset):
                # deliver block from REMOTE_CACHE to current cache
                if not found_in_remote_cache:
                    self.deliver_block(source=BlockSource.REMOTE_CACHE, op=MemOperation.PR_LOAD_MISS, target_id=id, tag=tag, cache_index=cache_index, offset=offset)
                    found_in_remote_cache = True
        if found_in_remote_cache:
            return BlockSource.REMOTE_CACHE
        else:
            self.deliver_block(source=BlockSource.MEMORY, op=MemOperation.PR_LOAD_MISS, target_id=id, tag=tag, cache_index=cache_index, offset=offset)
            return BlockSource.MEMORY

    def pr_store_miss_request(self, id, tag, cache_index, offset):
        found_in_remote_cache = False
        for c in self.caches:
            # If bus finds a valid copy in one of the caches
            if c.id != id and c.bus_update_load(tag, cache_index, offset):  # If any copy exists in remote cache, change to shared_clean
                if not found_in_remote_cache:
                    # deliver block from REMOTE_CACHE to current cache
                    self.deliver_block(source=BlockSource.REMOTE_CACHE, op=MemOperation.PR_STORE_MISS, target_id=id, tag=tag, cache_index=cache_index, offset=offset)
                    found_in_remote_cache = True

        if found_in_remote_cache:
            return BlockSource.REMOTE_CACHE # State of cache will be shared_clean
        else:
            self.deliver_block(source=BlockSource.MEMORY, op=MemOperation.PR_STORE_MISS, target_id=id, tag=tag, cache_index=cache_index, offset=offset)
            return BlockSource.MEMORY

    """
    bus_update_request: Called when a processor writes to a word that's contained in another remote cache.
    Obtain ownership for the cache that requested update.
    All other caches are changed to shared_clean if they originally owned block.
    Bus delivers word to all other caches
    """
    def bus_update_request(self, id, tag, cache_index, offset):
        for c in self.caches:
            if c.id != id and c.find_block(tag=tag, cache_index=cache_index) > -1:
                self.tracker.track_update(updates=1)
                self.deliver_word(source=BlockSource.REMOTE_CACHE, op=MemOperation.BUS_UPDATE_UPDATE, target_id=c.id, tag=tag, cache_index=cache_index, offset=offset)

    ########## Utility
    def flush_request(self, id, tag, cache_index, offset):
        for c in self.caches:
            if c.id != id:
                c.flush(tag, cache_index, offset)
   
    def deliver_block(self, source: BlockSource, op: MemOperation, target_id: int, tag: int, cache_index: int, offset: int):
        # self.log(f'Delivering block from {source} to {target_id}')
        for c in self.caches:
            if c.id == target_id:
                c.receive_block_from_bus(source, op, tag, cache_index, offset)
                self.tracker.track_traffic(word_size=self.cache_config.word_size, words=int(self.cache_config.block_size / self.cache_config.word_size))
                return

    def deliver_word(self, source: BlockSource, op: MemOperation, target_id: int, tag: int, cache_index: int, offset: int):
        self.log(f'Delivering word from {source} to {target_id}')
        for c in self.caches:
            if c.id == target_id:
                c.receive_word_from_bus(source, op, tag, cache_index, offset)
                self.tracker.track_traffic(word_size=self.cache_config.word_size, words=1)
                return

    def log(self, message: str):
        print(f'--- BUS: {message}')

    def print_stats(self):
        print(f'##### STATS FOR SHARED BUS #####')
        print(f'Data traffic: {self.tracker.data_traffic} bytes')
        print(f'Number of invalidations: {self.tracker.num_invalidation}')
        print(f'Number of updates: {self.tracker.num_update}')