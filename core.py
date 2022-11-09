from cache import Cache
from tracker import CoreTracker

class Core:
    def __init__(self, cache: Cache, tracker: CoreTracker) -> None:
        self.cache = cache
        self.tracker = tracker