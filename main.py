import sys
from system import System, Protocol
from cache import CacheConfig

def preprocess_data(data: str):
    split_lines = data.split('\n')
    res = []
    
    for line in split_lines:
        if len(line.split(' ')) == 2:
            label, value = line.split(' ')
            label = int(label)
            res.append((label, value))
    
    return res

if __name__ == "__main__":
    protocol = sys.argv[1]              # MESI or DRAGON
    if protocol == "MESI":
        protocol = Protocol.MESI
    elif protocol == "DRAGON":
        protocol = Protocol.DRAGON
    elif protocol == "MOESI":
        protocol = Protocol.MOESI
    else:
        protocol = Protocol.NONE
    
    trace = sys.argv[2]                 # bodytrack, blackscholes, fluidanimate
    cache_size = int(sys.argv[3])       # Default 4000 bytes (4KB)
    associativity = int(sys.argv[4])    # Default 2-way
    block_size = int(sys.argv[5])       # Default 32 bytes
    word_size = 4                       # Default 4 bytes
    processor_num = 4                   # Default 4 processors
    
    print(f'Protocol: {protocol}\nTrace file: {trace}\nCache size: {cache_size} bytes\nAssociativiy: {associativity}-way\nBlock size: {block_size} bytes')

    cacheConfig = CacheConfig(size=cache_size, associativity=associativity, block_size=block_size, word_size=word_size, protocol=protocol)
    system = System(protocol=protocol, processor_num=processor_num, cache_config=cacheConfig)

    # Read trace file and feed to system
    for i in range(0, processor_num):
        trace_filename = f'traces/{trace}_{i}.data'
        data = open(trace_filename, "r")
        data = data.read()
        data = preprocess_data(data)
        system.add_thread(data=data, core_id=i)

    system.trace()
