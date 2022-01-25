
from fHDHR.exceptions import TunerError

from .tuner import Tuner
from .stream.direct_m3u8_stream import m3u8_quality


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

            if (not hasattr(self.origins.origins_dict[origin], 'stream_method') or
               not self.origins.origins_dict[origin].stream_method):
                self.origins.origins_dict[origin].stream_method = self.streaming_method

        self.alt_stream_handlers = {}

    @property
    def streaming_method(self):
        """
        Method to use for streaming.
        """

        if not self.fhdhr.config.dict["streaming"]["method"]:
            return "direct"

        if self.fhdhr.config.dict["streaming"]["method"] not in self.streaming_methods:
            return "direct"

        return self.fhdhr.config.dict["streaming"]["method"]

    @property
    def streaming_methods(self):
        """
        List valid streaming methods.
        """

        streaming_methods = ["direct", "passthrough"]

        for plugin_name in list(self.fhdhr.plugins.plugins.keys()):

            if self.fhdhr.plugins.plugins[plugin_name].type == "alt_stream":
                streaming_methods.append(self.fhdhr.plugins.plugins[plugin_name].name)

        return streaming_methods

    def alt_stream_methods_selfadd(self):
        """
        Import stream methods.
        """

        self.fhdhr.logger.info("Detecting and Opening any found Stream Method plugins.")
        for plugin_name in list(self.fhdhr.plugins.plugins.keys()):

            if self.fhdhr.plugins.plugins[plugin_name].type == "alt_stream":
                method = self.fhdhr.plugins.plugins[plugin_name].name
                self.alt_stream_handlers[method] = self.fhdhr.plugins.plugins[plugin_name]

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

    def get_stream_info(self, stream_args):
        """
        Attempt to gather info on a stream.
        """

        self.fhdhr.logger.debug("Attempting to gather stream information for %s channel %s %s %s." %
                                (stream_args["origin"], stream_args["channel"],
                                 stream_args["channel_name"],
                                 stream_args["channel_callsign"]))

        stream_info = self.channels.get_channel_stream(stream_args, stream_args["origin"])
        if not stream_info:
            raise TunerError("806 - Tune Failed")

        if isinstance(stream_info, str):
            stream_info = {"url": stream_info, "headers": None}
        stream_args["stream_info"] = stream_info

        if not stream_args["stream_info"]["url"]:
            raise TunerError("806 - Tune Failed")

        if "headers" not in list(stream_args["stream_info"].keys()):
            stream_args["stream_info"]["headers"] = None

        # Set parameters for HTTP/s protocols
        if stream_args["stream_info"]["url"].startswith(tuple(["http://", "https://"])):

            try:
                channel_stream_url_headers = self.fhdhr.web.session.head(stream_args["stream_info"]["url"]).headers
                stream_args["true_content_type"] = channel_stream_url_headers['Content-Type']

            except self.fhdhr.web.exceptions.MissingSchema:
                raise TunerError("806 - Tune Failed")

            except self.fhdhr.web.exceptions.ConnectionError:
                raise TunerError("806 - Tune Failed")

            except KeyError:

                # Set for M3U8
                if stream_args["stream_info"]["url"].endswith(".m3u8"):
                    self.fhdhr.logger.warning("Stream Headers couldn't be properly determined, defaulting to application/text as content_type.")
                    stream_args["true_content_type"] = "application/text"
                    stream_args["content_type"] = "video/mpeg"

                else:
                    self.fhdhr.logger.warning("Stream Headers couldn't be properly determined, defaulting to video/mpeg as content_type.")
                    stream_args["true_content_type"] = "video/mpeg"
                    stream_args["content_type"] = "video/mpeg"

            if stream_args["true_content_type"].startswith(tuple(["application/", "text/"])):

                stream_args["content_type"] = "video/mpeg"
                if stream_args["origin_quality"] != -1:
                    stream_args["stream_info"]["url"] = m3u8_quality(self, stream_args)

            else:
                stream_args["content_type"] = stream_args["true_content_type"]

        # Set parameters for file://
        elif stream_args["stream_info"]["url"].startswith(tuple(["file://"])):
            # TODO some attempt to determine this information properly
            stream_args["true_content_type"] = "video/mpeg"
            stream_args["content_type"] = "video/mpeg"

        # Set parameters for RTP/s protocols
        elif stream_args["stream_info"]["url"].startswith(tuple(["rtp://", "rtsp://"])):
            # TODO some attempt to determine this information properly
            stream_args["true_content_type"] = "video/mpeg"
            stream_args["content_type"] = "video/mpeg"

        # Set parameters for UDP protocol
        elif stream_args["stream_info"]["url"].startswith(tuple(["udp://"])):
            # TODO some attempt to determine this information properly
            stream_args["true_content_type"] = "video/mpeg"
            stream_args["content_type"] = "video/mpeg"

        # Set parameters for Hardware Devices
        elif stream_args["stream_info"]["url"].startswith(tuple(["/dev/", "file://dev/"])):
            # TODO some attempt to determine this information properly
            stream_args["true_content_type"] = "video/mpeg"
            stream_args["content_type"] = "video/mpeg"

        # Set parameters for fallback
        else:
            self.fhdhr.logger.warning("Stream Method couldn't be properly determined, defaulting to video/mpeg as content_type.")
            stream_args["true_content_type"] = "video/mpeg"
            stream_args["content_type"] = "video/mpeg"

        return stream_args
