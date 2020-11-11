import threading
import datetime

from fHDHR.exceptions import TunerError
from fHDHR.tools import humanized_time


class Tuner():
    def __init__(self, fhdhr, inum, epg):
        self.fhdhr = fhdhr
        self.number = inum
        self.epg = epg
        self.tuner_lock = threading.Lock()
        self.set_off_status()

    def grab(self, stream_args):
        if self.tuner_lock.locked():
            raise TunerError("Tuner #" + str(self.number) + " is not available.")

        self.fhdhr.logger.info("Tuner #" + str(self.number) + " to be used for stream.")
        self.tuner_lock.acquire()
        self.status = {
                        "status": "Active",
                        "method": stream_args["method"],
                        "accessed": stream_args["accessed"],
                        "channel": stream_args["channel"],
                        "proxied_url": stream_args["channelUri"],
                        "time_start": datetime.datetime.utcnow(),
                        }

    def close(self):
        self.fhdhr.logger.info("Tuner #" + str(self.number) + " Shutting Down.")
        self.set_off_status()
        self.tuner_lock.release()

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


class Tuners():

    def __init__(self, fhdhr, epg):
        self.fhdhr = fhdhr

        self.epg = epg
        self.max_tuners = int(self.fhdhr.config.dict["fhdhr"]["tuner_count"])

        self.tuners = {}

        for i in range(1, self.max_tuners + 1):
            self.tuners[i] = Tuner(fhdhr, i, epg)

    def tuner_grab(self, stream_args):
        tunerselected = None

        if stream_args["tuner"]:
            if int(stream_args["tuner"]) not in list(self.tuners.keys()):
                raise TunerError("Tuner " + str(stream_args["tuner"]) + " does not exist.")
            self.tuners[int(stream_args["tuner"])].grab(stream_args)
            tunerselected = int(stream_args["tuner"])

        else:

            for tunernum in range(1, self.max_tuners + 1):
                try:
                    self.tuners[int(tunernum)].grab(stream_args)
                except TunerError:
                    continue
                else:
                    tunerselected = tunernum
                    break

        if not tunerselected:
            raise TunerError("No Available Tuners.")
        else:
            return tunerselected

    def tuner_close(self, tunernum):
        self.tuners[int(tunernum)].close()

    def status(self):
        all_status = {}
        for tunernum in range(1, self.max_tuners + 1):
            all_status[tunernum] = self.tuners[int(tunernum)].get_status()
        return all_status

    def available_tuner_count(self):
        available_tuners = 0
        for tunernum in range(1, self.max_tuners + 1):
            tuner_status = self.tuners[int(tunernum)].get_status()
            if tuner_status["status"] == "Inactive":
                available_tuners += 1
        return available_tuners

    def inuse_tuner_count(self):
        inuse_tuners = 0
        for tunernum in range(1, self.max_tuners + 1):
            tuner_status = self.tuners[int(tunernum)].get_status()
            if tuner_status["status"] == "Active":
                inuse_tuners += 1
        return inuse_tuners
