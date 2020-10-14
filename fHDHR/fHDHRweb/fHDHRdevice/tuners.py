import threading

from fHDHR.fHDHRerrors import TunerError


class Tuner():
    def __init__(self, inum):
        self.number = inum
        self.tuner_lock = threading.Lock()
        self.status = {}

    def grab(self, stream_args):
        if self.tuner_lock.locked():
            raise TunerError("Tuner #" + str(self.number) + " is not available.")

        print("Tuner #" + str(self.number) + " to be used for stream.")
        self.tuner_lock.acquire()
        self.status = {
                        "status": "Active",
                        "method": stream_args["method"],
                        "accessed": stream_args["accessed"],
                        "proxied_url": stream_args["channelUri"],
                        }

    def close(self):
        print("Tuner #" + str(self.number) + " Shutting Down.")
        self.status = {}
        self.tuner_lock.release()

    def get_status(self):
        if not self.tuner_lock.locked():
            return {"status": "Inactive"}
        return self.status


class Tuners():

    def __init__(self, settings):
        self.config = settings
        self.max_tuners = int(self.config.dict["fhdhr"]["tuner_count"])

        for i in range(1, self.max_tuners + 1):
            exec("%s = %s" % ("self.tuner_" + str(i), "Tuner(i)"))

    def tuner_grab(self, stream_args, tunernum=None):
        tunerselected = None

        if tunernum:
            if tunernum not in range(1, self.max_tuners + 1):
                raise TunerError("Tuner " + str(tunernum) + " does not exist.")
            eval("self.tuner_" + str(tunernum) + ".grab(stream_args)")
            tunerselected = tunernum

        else:

            for tunernum in range(1, self.max_tuners + 1):
                try:
                    eval("self.tuner_" + str(tunernum) + ".grab(stream_args)")
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
        eval("self.tuner_" + str(tunernum) + ".close()")

    def status(self):
        all_status = {}
        for tunernum in range(1, self.max_tuners + 1):
            all_status[tunernum] = eval("self.tuner_" + str(tunernum) + ".get_status()")
        return all_status
