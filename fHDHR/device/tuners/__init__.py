
from fHDHR.exceptions import TunerError

from .tuner import Tuner


class Tuners():

    def __init__(self, fhdhr, epg, channels):
        self.fhdhr = fhdhr
        self.channels = channels

        self.epg = epg
        self.max_tuners = int(self.fhdhr.config.dict["fhdhr"]["tuner_count"])

        self.tuners = {}

        self.fhdhr.logger.info("Creating %s tuners." % str(self.max_tuners))

        for i in range(0, self.max_tuners):
            self.tuners[str(i)] = Tuner(fhdhr, i, epg)

    def get_available_tuner(self):
        return next(tunernum for tunernum in list(self.tuners.keys()) if not self.tuners[tunernum].tuner_lock.locked()) or None

    def get_scanning_tuner(self):
        return next(tunernum for tunernum in list(self.tuners.keys()) if self.tuners[tunernum].status["status"] == "Scanning") or None

    def stop_tuner_scan(self):
        tunernum = self.get_scanning_tuner()
        if tunernum:
            self.tuners[str(tunernum)].close()

    def tuner_scan(self):
        """Temporarily use a tuner for a scan"""
        if not self.available_tuner_count():
            raise TunerError("805 - All Tuners In Use")

        tunernumber = self.get_available_tuner()
        self.tuners[str(tunernumber)].channel_scan()

        if not tunernumber:
            raise TunerError("805 - All Tuners In Use")

    def tuner_grab(self, tuner_number, channel_number):

        if str(tuner_number) not in list(self.tuners.keys()):
            self.fhdhr.logger.error("Tuner %s does not exist." % str(tuner_number))
            raise TunerError("806 - Tune Failed")

        # TunerError will raise if unavailable
        self.tuners[str(tuner_number)].grab(channel_number)

        return tuner_number

    def first_available(self, channel_number, dograb=True):

        if not self.available_tuner_count():
            raise TunerError("805 - All Tuners In Use")

        tunernumber = self.get_available_tuner()

        if not tunernumber:
            raise TunerError("805 - All Tuners In Use")
        else:
            self.tuners[str(tunernumber)].grab(channel_number)
            return tunernumber

    def tuner_close(self, tunernum):
        self.tuners[str(tunernum)].close()

    def status(self):
        all_status = {}
        for tunernum in list(self.tuners.keys()):
            all_status[tunernum] = self.tuners[str(tunernum)].get_status()
        return all_status

    def available_tuner_count(self):
        available_tuners = 0
        for tunernum in list(self.tuners.keys()):
            if not self.tuners[str(tunernum)].tuner_lock.locked():
                available_tuners += 1
        return available_tuners

    def inuse_tuner_count(self):
        inuse_tuners = 0
        for tunernum in list(self.tuners.keys()):
            if self.tuners[str(tunernum)].tuner_lock.locked():
                inuse_tuners += 1
        return inuse_tuners

    def get_stream_info(self, stream_args):

        stream_info = self.channels.get_channel_stream(stream_args)
        if not stream_info:
            raise TunerError("806 - Tune Failed")

        if isinstance(stream_info, str):
            stream_info = {"url": stream_info}
        stream_args["stream_info"] = stream_info

        if not stream_args["stream_info"]["url"]:
            raise TunerError("806 - Tune Failed")

        if stream_args["stream_info"]["url"].startswith("udp://"):
            stream_args["true_content_type"] = "video/mpeg"
            stream_args["content_type"] = "video/mpeg"
        else:

            channel_stream_url_headers = self.fhdhr.web.session.head(stream_args["stream_info"]["url"]).headers
            stream_args["true_content_type"] = channel_stream_url_headers['Content-Type']

            if stream_args["true_content_type"].startswith(tuple(["application/", "text/"])):
                stream_args["content_type"] = "video/mpeg"
            else:
                stream_args["content_type"] = stream_args["true_content_type"]

        return stream_args
