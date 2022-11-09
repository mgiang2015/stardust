import sys
from cache import Cache
from system import System, Protocol, CacheConfig

if __name__ == "__main__":
    protocol = sys.argv[1]              # MESI or DRAGON
    if protocol == "MESI":
        protocol = Protocol.MESI
    elif protocol == "DRAGON":
        protocol = Protocol.DRAGON
    else:
        protocol = Protocol.NONE
    
    trace_file = sys.argv[2]            # bodytrack, blackscholes, fluidanimate
    cache_size = int(sys.argv[3])       # Default 4000 bytes (4KB)
    associativity = int(sys.argv[4])    # Default 2-way
    block_size = int(sys.argv[5])       # Default 32 bytes
    word_size = 4                       # Default 4 bytes
    processor_num = 4                   # Default 4 processors
    
    print(f'Protocol: {protocol}\nTrace file: {trace_file}\nCache size: {cache_size} bytes\nAssociativiy: {associativity}-way\nBlock size: {block_size} bytes')

    cacheConfig = CacheConfig(size=cache_size, associativity=associativity, block_size=block_size, word_size=word_size)
    system = System(protocol=protocol, processor_num=processor_num, cache_config=CacheConfig)
