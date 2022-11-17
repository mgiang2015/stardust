from enum import Enum

class Instruction(Enum):
    LOAD = 0
    STORE = 1
    OTHERS = 2

class Protocol(Enum):
    MESI = 0
    DRAGON = 1
    MOESI = 2
    NONE = 3

class BlockState(Enum):
    MODIFIED = 0
    EXCLUSIVE = 1
    SHARED = 2
    INVALID = 3
    SHARED_CLEAN = 4
    SHARED_MODIFIED = 5
    DIRTY = 6

class MemOperation(Enum):
    # Invalidation-based operations
    PR_INVALIDATE_LOAD = 0
    PR_INVALIDATE_STORE = 1
    BUS_INVALIDATE_LOAD = 2
    BUS_LOAD_EXCLUSIVE = 5
    # Update-based operations
    PR_STORE_MISS = 6
    PR_LOAD_MISS = 8
    PR_UPDATE_STORE = 7
    BUS_UPDATE_LOAD = 3
    BUS_UPDATE_UPDATE = 4

class BlockSource(Enum):
    LOCAL_CACHE = 0
    REMOTE_CACHE = 1
    MEMORY = 2