
from .watch import Watch
from .tuner import Tuner


class fHDHR_WATCH():

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

        self.watch = Watch(fhdhr)
        self.tuner = Tuner(fhdhr)
