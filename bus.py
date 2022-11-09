from tracker import BusTracker

# shared bus class
class Bus:
    def __init__(self, tracker: BusTracker) -> None:
        self.tracker = tracker