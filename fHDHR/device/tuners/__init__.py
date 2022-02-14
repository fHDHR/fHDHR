
from fHDHR.exceptions import TunerError

from .tuner import Tuner


class Tuners():
    """
    fHDHR emulated Tuners system.
    """

    def __init__(self, fhdhr, epg, channels, origins):
        self.fhdhr = fhdhr
        self.channels = channels
        self.origins = origins
        self.epg = epg

        self.fhdhr.logger.info("Initializing Tuners system")

        self.tuners = {}
        for origin in list(self.origins.origins_dict.keys()):
            self.tuners[origin] = {}

            max_tuners = int(self.origins.origins_dict[origin].tuners)

            self.fhdhr.logger.info("Creating %s tuners for %s." % (max_tuners, origin))

            for i in range(0, max_tuners):
                self.tuners[origin][str(i)] = Tuner(fhdhr, i, epg, origin)

    def get_available_tuner(self, origin):
        """
        Get an available tuner
        """

        for tunernum in list(self.tuners[origin].keys()):

            if not self.tuners[origin][tunernum].tuner_lock.locked():
                return tunernum

        return None

    def get_scanning_tuner(self, origin):
        """
        Find what tuner is scanning.
        """

        for tunernum in list(self.tuners[origin].keys()):

            if self.tuners[origin][tunernum].status["status"] == "Scanning":
                return tunernum

        return None

    def stop_tuner_scan(self, origin):
        """
        Stop a Tuner Scan.
        """

        tunernum = self.get_scanning_tuner(origin)
        if tunernum:
            self.tuners[origin][str(tunernum)].close()

    def tuner_scan(self, origin="all"):
        """
        Temporarily use a tuner for a scan.
        """

        if origin == "all":
            origins = list(self.tuners.keys())
        else:
            origins = [origin]

        for origin in origins:

            if not self.available_tuner_count(origin):
                raise TunerError("805 - All Tuners In Use")

            tunernumber = self.get_available_tuner(origin)
            self.tuners[origin][str(tunernumber)].channel_scan(origin)

            if not tunernumber:
                raise TunerError("805 - All Tuners In Use")

    def tuner_grab(self, tuner_number, origin, channel_number):
        """
        Attempt to grab a tuner.
        """

        if str(tuner_number) not in list(self.tuners[origin].keys()):
            self.fhdhr.logger.error("Tuner %s does not exist for %s." % (tuner_number, origin))
            raise TunerError("806 - Tune Failed")

        # TunerError will raise if unavailable
        self.tuners[origin][str(tuner_number)].grab(origin, channel_number)

        return tuner_number

    def first_available(self, origin, channel_number, dograb=True):
        """
        Grab first avaiable tuner.
        """

        if not self.available_tuner_count(origin):
            raise TunerError("805 - All Tuners In Use")

        tunernumber = self.get_available_tuner(origin)

        if not tunernumber:
            raise TunerError("805 - All Tuners In Use")
        else:
            self.tuners[origin][str(tunernumber)].grab(origin, channel_number)
            return tunernumber

    def tuner_close(self, tunernum, origin):
        """
        Close a tuner.
        """

        self.tuners[origin][str(tunernum)].close()

    def status(self, origin=None):
        """
        Get Tuners status.
        """

        all_status = {}
        if origin:

            for tunernum in list(self.tuners[origin].keys()):
                all_status[tunernum] = self.tuners[origin][str(tunernum)].get_status()

        else:

            for origin in list(self.tuners.keys()):

                all_status[origin] = {}
                for tunernum in list(self.tuners[origin].keys()):
                    all_status[origin][tunernum] = self.tuners[origin][str(tunernum)].get_status()

        return all_status

    def available_tuner_count(self, origin):
        """
        Return number of Avaiable tuners.
        """

        available_tuners = 0
        for tunernum in list(self.tuners[origin].keys()):

            if not self.tuners[origin][str(tunernum)].tuner_lock.locked():
                available_tuners += 1

        return available_tuners

    def inuse_tuner_count(self, origin):
        """
        Return number of tuners being used.
        """

        inuse_tuners = 0
        for tunernum in list(self.tuners[origin].keys()):

            if self.tuners[origin][str(tunernum)].tuner_lock.locked():
                inuse_tuners += 1

        return inuse_tuners
