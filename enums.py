from enum import Enum

class Instruction(Enum):
    LOAD = 0
    STORE = 1
    OTHERS = 2

class Protocol(Enum):
    MESI = 0
    DRAGON = 1
    NONE = 2

class BlockState(Enum):
    MODIFIED = 0
    EXCLUSIVE = 1
    SHARED = 2
    INVALID = 3

class MemOperation(Enum):
    PR_LOAD = 0
    PR_STORE = 1
    BUS_LOAD = 2
    BUS_STORE = 3
    BUS_LOAD_EXCLUSIVE = 4
    FLUSH = 5

class BlockSource(Enum):
    LOCAL_CACHE = 0
    REMOTE_CACHE = 1
    MEMORY = 2