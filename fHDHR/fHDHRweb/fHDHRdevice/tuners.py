import threading

from fHDHR.fHDHRerrors import TunerError


class Tuners():

    def __init__(self, settings):
        self.config = settings

        self.max_tuners = int(self.config.dict["fhdhr"]["tuner_count"])
        self.tuners = self.max_tuners
        self.tuner_lock = threading.Lock()

    def tuner_grab(self):
        self.tuner_lock.acquire()
        if self.tuners == 0:
            self.tuner_lock.release()
            raise TunerError("No Available Tuners.")
        self.tuners -= 1
        self.tuner_lock.release()

    def tuner_close(self):
        self.tuner_lock.acquire()
        self.tuners += 1
        self.tuner_lock.release()
