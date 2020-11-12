import threading
import datetime

from fHDHR.exceptions import TunerError
from fHDHR.tools import humanized_time

from .stream import Stream


class Tuner():
    def __init__(self, fhdhr, inum, epg):
        self.fhdhr = fhdhr

        self.number = inum
        self.epg = epg

        self.tuner_lock = threading.Lock()
        self.set_off_status()

    def grab(self):
        if self.tuner_lock.locked():
            self.fhdhr.logger.error("Tuner #" + str(self.number) + " is not available.")
            raise TunerError("804 - Tuner In Use")
        self.tuner_lock.acquire()
        self.status["status"] = "Acquired"
        self.fhdhr.logger.info("Tuner #" + str(self.number) + " Acquired.")

    def close(self):
        self.set_off_status()
        if self.tuner_lock.locked():
            self.tuner_lock.release()
        self.fhdhr.logger.info("Tuner #" + str(self.number) + " Released.")

    def get_status(self):
        current_status = self.status.copy()
        if current_status["status"] == "Active":
            current_status["Play Time"] = str(
                humanized_time(
                    int((datetime.datetime.utcnow() - current_status["time_start"]).total_seconds())))
            current_status["time_start"] = str(current_status["time_start"])
            current_status["epg"] = self.epg.whats_on_now(current_status["channel"])
        return current_status

    def set_off_status(self):
        self.status = {"status": "Inactive"}

    def get_stream(self, stream_args, tuner):
        stream = Stream(self.fhdhr, stream_args, tuner)
        return stream.get()

    def set_status(self, stream_args):
        self.status = {
                        "status": "Active",
                        "method": stream_args["method"],
                        "accessed": stream_args["accessed"],
                        "channel": stream_args["channel"],
                        "proxied_url": stream_args["channelUri"],
                        "time_start": datetime.datetime.utcnow(),
                        }
