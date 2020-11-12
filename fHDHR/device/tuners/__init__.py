
from fHDHR.exceptions import TunerError

from .tuner import Tuner


class Tuners():

    def __init__(self, fhdhr, epg, channels):
        self.fhdhr = fhdhr
        self.channels = channels

        self.epg = epg
        self.max_tuners = int(self.fhdhr.config.dict["fhdhr"]["tuner_count"])

        self.tuners = {}

        for i in range(1, self.max_tuners + 1):
            self.tuners[i] = Tuner(fhdhr, i, epg)

    def tuner_grab(self, tuner_number):

        if int(tuner_number) not in list(self.tuners.keys()):
            self.fhdhr.logger.error("Tuner %s does not exist." % str(tuner_number))
            raise TunerError("806 - Tune Failed")

        # TunerError will raise if unavailable
        self.tuners[int(tuner_number)].grab()

        return tuner_number

    def first_available(self):

        if not self.available_tuner_count():
            raise TunerError("805 - All Tuners In Use")

        for tunernum in list(self.tuners.keys()):
            try:
                self.tuners[int(tunernum)].grab()
            except TunerError:
                continue
            else:
                return tunernum

        raise TunerError("805 - All Tuners In Use")

    def tuner_close(self, tunernum):
        self.tuners[int(tunernum)].close()

    def status(self):
        all_status = {}
        for tunernum in list(self.tuners.keys()):
            all_status[tunernum] = self.tuners[int(tunernum)].get_status()
        return all_status

    def available_tuner_count(self):
        available_tuners = 0
        for tunernum in list(self.tuners.keys()):
            tuner_status = self.tuners[int(tunernum)].get_status()
            if tuner_status["status"] == "Inactive":
                available_tuners += 1
        return available_tuners

    def inuse_tuner_count(self):
        inuse_tuners = 0
        for tunernum in list(self.tuners.keys()):
            tuner_status = self.tuners[int(tunernum)].get_status()
            if tuner_status["status"] == "Active":
                inuse_tuners += 1
        return inuse_tuners

    def get_stream_info(self, stream_args):

        stream_args["channelUri"] = self.channels.get_channel_stream(str(stream_args["channel"]))
        if not stream_args["channelUri"]:
            raise TunerError("806 - Tune Failed")

        channelUri_headers = self.fhdhr.web.session.head(stream_args["channelUri"]).headers
        stream_args["true_content_type"] = channelUri_headers['Content-Type']

        if stream_args["true_content_type"].startswith("application/"):
            stream_args["content_type"] = "video/mpeg"
        else:
            stream_args["content_type"] = stream_args["true_content_type"]

        return stream_args
