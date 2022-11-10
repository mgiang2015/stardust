from tracker import BusTracker
from cache import Cache
from enums import BlockSource, MemOperation

# shared bus class
class Bus:
    def __init__(self, tracker: BusTracker) -> None:
        self.tracker = tracker
        self.caches = []

    def add_cache(self, cache: Cache):
        self.caches.append(cache)

    def load_request(self, id, tag, cache_index, offset) -> BlockSource:
        self.log(f'Received load_request from core {id} with tag {tag}, index {cache_index} and offset {offset}')
        for c in self.caches:
            # If bus finds a valid copy in one of the caches
            if c.id != id and c.bus_load(tag, cache_index, offset):
                # deliver block from REMOTE_CACHE to current cache
                self.deliver_block(source=BlockSource.REMOTE_CACHE, op=MemOperation.PR_LOAD, target_id=id, tag=tag, cache_index=cache_index, offset=offset)
                return BlockSource.REMOTE_CACHE
        
        self.deliver_block(source=BlockSource.MEMORY, op=MemOperation.PR_LOAD, target_id=id, tag=tag, cache_index=cache_index, offset=offset)
        return BlockSource.MEMORY

    def deliver_block(self, source: BlockSource, op: MemOperation, target_id: int, tag: int, cache_index: int, offset: int):
        self.log(f'Delivering block from {source} to {target_id}')
        for c in self.caches:
            if c.id == target_id:
                c.receive_block_from_bus(source, op, tag, cache_index, offset)
                return

    def log(self, message: str):
        print(f'--- BUS: {message}')