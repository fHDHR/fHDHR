
from fHDHR.exceptions import TunerError

from .tuner import Tuner


class Tuners():
    """
    fHDHR emulated Tuners system.
    """

    def __init__(self, fhdhr, epg, origins):
        self.fhdhr = fhdhr
        self.origins = origins
        self.epg = epg

        self.fhdhr.logger.info("Initializing Tuners system")

        self.tuners = {}
        for origin_name in self.origins.list_origins:
            self.tuners[origin_name] = {}

            max_tuners = int(self.origins.get_origin_property(origin_name, "tuners"))
            # TODO dynamically adjust

            self.fhdhr.logger.info("Creating %s tuners for %s." % (max_tuners, origin_name))

            for i in range(0, max_tuners):
                self.tuners[origin_name][str(i)] = Tuner(fhdhr, i, epg, origin_name)

    def get_available_tuner(self, origin_name):
        """
        Get an available tuner
        """

        for tunernum in list(self.tuners[origin_name].keys()):

            if not self.tuners[origin_name][tunernum].tuner_lock.locked():
                return tunernum

        return None

    def get_scanning_tuner(self, origin_name):
        """
        Find what tuner is scanning.
        """

        for tunernum in list(self.tuners[origin_name].keys()):

            if self.tuners[origin_name][tunernum].status["status"] == "Scanning":
                return tunernum

        return None

    def stop_tuner_scan(self, origin_name):
        """
        Stop a Tuner Scan.
        """

        tunernum = self.get_scanning_tuner(origin_name)
        if tunernum:
            self.tuners[origin_name][str(tunernum)].close()

    def tuner_scan(self, origin_name="all"):
        """
        Temporarily use a tuner for a scan.
        """

        if origin_name == "all":
            origins = list(self.tuners.keys())
        else:
            origins = [origin_name]

        for origin_name in origins:

            if not self.available_tuner_count(origin_name):
                raise TunerError("805 - All Tuners In Use")

            tunernumber = self.get_available_tuner(origin_name)
            self.tuners[origin_name][str(tunernumber)].channel_scan(origin_name)

            if not tunernumber:
                raise TunerError("805 - All Tuners In Use")

    def tuner_grab(self, tuner_number, origin_name, channel_number):
        """
        Attempt to grab a tuner.
        """

        if str(tuner_number) not in list(self.tuners[origin_name].keys()):
            self.fhdhr.logger.error("Tuner %s does not exist for %s." % (tuner_number, origin_name))
            raise TunerError("806 - Tune Failed")

        # TunerError will raise if unavailable
        self.tuners[origin_name][str(tuner_number)].grab(origin_name, channel_number)

        return tuner_number

    def first_available(self, origin_name, channel_number, dograb=True):
        """
        Grab first avaiable tuner.
        """

        if not self.available_tuner_count(origin_name):
            raise TunerError("805 - All Tuners In Use")

        tunernumber = self.get_available_tuner(origin_name)

        if not tunernumber:
            raise TunerError("805 - All Tuners In Use")
        else:
            self.tuners[origin_name][str(tunernumber)].grab(origin_name, channel_number)
            return tunernumber

    def tuner_close(self, tunernum, origin_name):
        """
        Close a tuner.
        """

        self.tuners[origin_name][str(tunernum)].close()

    def status(self, origin_name=None):
        """
        Get Tuners status.
        """

        all_status = {}
        if origin_name:

            for tunernum in list(self.tuners[origin_name].keys()):
                all_status[tunernum] = self.tuners[origin_name][str(tunernum)].get_status()

        else:

            for origin_name in list(self.tuners.keys()):

                all_status[origin_name] = {}
                for tunernum in list(self.tuners[origin_name].keys()):
                    all_status[origin_name][tunernum] = self.tuners[origin_name][str(tunernum)].get_status()

        return all_status

    def available_tuner_count(self, origin_name):
        """
        Return number of Avaiable tuners.
        """

        available_tuners = 0
        for tunernum in list(self.tuners[origin_name].keys()):

            if not self.tuners[origin_name][str(tunernum)].tuner_lock.locked():
                available_tuners += 1

        return available_tuners

    def inuse_tuner_count(self, origin_name):
        """
        Return number of tuners being used.
        """

        inuse_tuners = 0
        for tunernum in list(self.tuners[origin_name].keys()):

            if self.tuners[origin_name][str(tunernum)].tuner_lock.locked():
                inuse_tuners += 1

        return inuse_tuners
