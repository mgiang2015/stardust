class CacheConfig:
    def __init__(self, size: int, associativity: int, block_size: int, word_size: int) -> None:
        self.size = size
        self.associativity = associativity
        self.block_size = block_size
        self.word_size = word_size

# L1 Cache. Each cache has cache config
# Each cache has 125 cache lines of size 32 bytes each
class Cache:
    def __init__(self, cache_config: CacheConfig) -> None:
        self.config = cache_config