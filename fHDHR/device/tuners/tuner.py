import threading
import datetime

from fHDHR.exceptions import TunerError


class Tuner():
    """
    fHDHR Tuner Object.
    """

    def __init__(self, fhdhr, inum, epg, origin_name):
        self.fhdhr = fhdhr

        self.number = inum
        self.origin_name = origin_name
        self.epg = epg

        self.tuner_lock = threading.Lock()
        self.set_off_status()

        self.chanscan_url = "/api/channels?method=scan"
        self.close_url = "/api/tuners?method=close&tuner=%s&origin=%s" % (self.number, self.origin_name)
        self.start_url = "/api/tuners?method=start&tuner=%s&origin=%s" % (self.number, self.origin_name)

    def channel_scan(self, origin_name, grabbed=False):
        """
        Use tuner to scan channels.
        """

        if self.tuner_lock.locked() and not grabbed:
            self.fhdhr.logger.error("%s Tuner #%s is not available." % (self.origin_name, self.number))
            raise TunerError("804 - Tuner In Use")

        if self.status["status"] == "Scanning":
            self.fhdhr.logger.info("Channel Scan Already In Progress!")

        else:

            if not grabbed:
                self.tuner_lock.acquire()

            self.status["status"] = "Scanning"
            self.status["origin_name"] = origin_name
            self.status["time_start"] = datetime.datetime.utcnow()
            self.fhdhr.logger.info("Tuner #%s Performing Channel Scan for %s origin." % (self.number, origin_name))

            chanscan = threading.Thread(target=self.runscan, args=(origin_name,))
            chanscan.start()

    def runscan(self, origin_name):
        """
        Use a threaded API call to scan channels.
        """

        self.fhdhr.api.get("%s&origin=%s" % (self.chanscan_url, origin_name))
        self.fhdhr.logger.info("Requested Channel Scan for %s origin Complete." % origin_name)
        self.close()
        self.fhdhr.api.threadget(self.close_url)

    def grab(self, origin_name, channel_number):
        """
        Grab Tuner.
        """

        if self.tuner_lock.locked():
            self.fhdhr.logger.error("Tuner #%s is not available." % self.number)
            raise TunerError("804 - Tuner In Use")

        self.tuner_lock.acquire()
        self.status["status"] = "Acquired"
        self.status["origin_name"] = origin_name
        self.status["channel"] = channel_number
        self.status["time_start"] = datetime.datetime.utcnow()
        self.fhdhr.logger.info("Tuner #%s Acquired." % str(self.number))

    def close(self):
        """
        Close Tuner.
        """

        self.set_off_status()

        if self.tuner_lock.locked():
            self.tuner_lock.release()
            self.fhdhr.logger.info("Tuner #%s Released." % self.number)

    def get_status(self):
        """
        Get Tuner Status.
        """

        current_status = self.status.copy()
        current_status["epg"] = {}

        if current_status["status"] in ["Acquired", "Active", "Scanning"]:
            current_status["running_time"] = str(
                self.fhdhr.time.humanized_time(
                    int((datetime.datetime.utcnow() - current_status["time_start"]).total_seconds())))
            current_status["time_start"] = str(current_status["time_start"])

        if current_status["status"] in ["Active"]:

            if current_status["origin_name"] in self.epg.epg_methods:
                current_status["epg"] = self.epg.whats_on_now(current_status["channel"], method=current_status["origin_name"])

        return current_status

    def set_off_status(self):
        """
        Set Off Status.
        """

        self.stream = None
        self.status = {"status": "Inactive"}

    def set_status(self, stream_args):
        """
        Set Tuner Status.
        """

        if self.status["status"] != "Active":
            self.status = {
                            "status": "Active",
                            "clients": [],
                            "clients_id": [],
                            "method": stream_args["method"],
                            "accessed": [stream_args["accessed"]],
                            "origin_name": stream_args["origin_name"],
                            "channel": stream_args["channel"],
                            "proxied_url": stream_args["stream_info"]["url"],
                            "time_start": datetime.datetime.utcnow(),
                            "downloaded_size": 0,
                            "downloaded_chunks": 0,
                            "served_size": 0,
                            "served_chunks": 0
                            }

        if stream_args["client"] not in self.status["clients"]:
            self.status["clients"].append(stream_args["client"])

        if stream_args["client_id"] not in self.status["clients_id"]:
            self.status["clients_id"].append(stream_args["client_id"])
