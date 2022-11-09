from cache import Cache
from tracker import CoreTracker

class Core:
    def __init__(self, id, cache: Cache, tracker: CoreTracker) -> None:
        self.cache = cache
        self.tracker = tracker
        self.id = id

    def trace(self, data) -> None:
        for label, value in data:
            print(f'Howdy from core {self.id}! Executing command {label} with value {value}')
