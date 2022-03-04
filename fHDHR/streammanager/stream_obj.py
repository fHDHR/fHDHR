from fHDHR.exceptions import TunerError

from .stream.direct_m3u8_stream import m3u8_quality

from .stream import Stream


class Stream_OBJ():

    def __init__(self, fhdhr, device, origins, alt_stream_handlers, request, session, chan_obj, stream_args):
        self.fhdhr = fhdhr
        self.device = device
        self.origins = origins
        self.alt_stream_handlers = alt_stream_handlers

        self.request = request
        self.session = session

        self.chan_obj = chan_obj
        self.stream_args = stream_args

        self.tuner = None

        self.setup_channel_stream()

        self.log_stream_request_info()

    @property
    def chan_dict(self):
        return self.chan_obj.dict

    @property
    def origin(self):
        return self.chan_obj.origin

    @property
    def origin_plugin(self):
        return self.fhdhr.origins.get_origin(self.origin)

    @property
    def tuner_needed(self):
        """Any reason a tuner might not be needed"""
        if self.stream_args["method"] == "passthrough":
            return False
        return True

    def add_downloaded_size(self, bytes_count, chunks_count):
        """
        Append size of total downloaded size and count.
        """

        if "downloaded_size" in list(self.tuner.status.keys()):
            self.tuner.status["downloaded_size"] += bytes_count
        else:
            self.tuner.status["downloaded_size"] = bytes_count

        self.tuner.status["downloaded_chunks"] = chunks_count

    def add_served_size(self, bytes_count, chunks_count):
        """
        Append Served size and count.
        """

        if "served_size" in list(self.tuner.status.keys()):
            self.tuner.status["served_size"] += bytes_count
        else:
            self.tuner.status["served_size"] = bytes_count

        self.tuner.status["served_chunks"] = chunks_count

    def log_stream_request_info(self):

        self.fhdhr.logger.info("Client has requested stream for %s." %
                               "%s channel %s %s %s" % (self.chan_obj.origin,
                                                        self.chan_obj.number,
                                                        self.chan_obj.name,
                                                        self.chan_obj.callsign))

        self.fhdhr.logger.info("Selected Stream Parameters:"
                               "method=%s duration=%s origin_quality=%s transcode_quality=%s." %
                               (self.stream_args["method"],
                                self.stream_args["duration"],
                                self.stream_args["origin_quality"],
                                self.stream_args["transcode_quality"]))

    def setup_channel_stream(self):
        self.get_origin_stream_info()

        self.validate_stream_url()

        if self.tuner_needed:
            self.tuner_acquire()

    def stream_restore(self):
        self.get_origin_stream_info()
        self.validate_stream_url()

    def tuner_acquire(self):
        self.fhdhr.logger.info("Attempting to Select an available tuner for this stream.")

        if not self.stream_args["tuner_number"]:
            tunernum = self.device.tuners.first_available(self.chan_obj.origin, self.chan_obj.number)
        else:
            tunernum = self.device.tuners.tuner_grab(self.stream_args["tuner_number"], self.chan_obj.origin, self.chan_obj.number)

        self.tuner = self.device.tuners.tuners[self.chan_obj.origin][str(tunernum)]
        self.fhdhr.logger.info("%s Tuner #%s to be used for stream." % (self.chan_obj.origin, tunernum))

        self.fhdhr.logger.info("Preparing Stream...")

        self.tuner.set_status(self.stream_args)
        self.session["tuner_used"] = tunernum

        self.stream = Stream(self.fhdhr, self.tuner, self)

    def get_origin_stream_info(self):
        """
        Pull Stream Information from Origin Plugin
        """
        stream_info_defaults = {"headers": None}

        # Pull Stream Info from Origin Plugin
        self.fhdhr.logger.debug("Attempting to gather stream information for %s channel %s %s %s." %
                                (self.stream_args["origin"], self.stream_args["channel"],
                                 self.stream_args["channel_name"],
                                 self.stream_args["channel_callsign"]))

        stream_info = self.fhdhr.origins.origins_dict[self.stream_args["origin"]].get_channel_stream(self.chan_dict, self.stream_args)
        if not stream_info:
            raise TunerError("806 - Tune Failed")

        if not stream_info:
            raise TunerError("806 - Tune Failed")

        # Format Information from Origin Plugin
        if isinstance(stream_info, str):
            stream_info = {"url": stream_info}

        # Fail if no url present
        if not stream_info["url"]:
            raise TunerError("806 - Tune Failed")

        # Add keys/values to stream_info if missing
        for default_key in list(stream_info_defaults.keys()):
            if default_key not in list(stream_info.keys()):
                stream_info[default_key] = stream_info_defaults[default_key]

        self.stream_args["stream_info"] = stream_info

    def validate_stream_url(self):
        """
        Validate Stream URL from Origin
        """

        # Make sure URL is not empty
        if "://" in self.stream_args["stream_info"]["url"]:
            if (not len(self.stream_args["stream_info"]["url"].split("://")[-1])
               or self.stream_args["stream_info"]["url"].split("://")[-1] == "None"):
                raise TunerError("806 - Tune Failed")

        # Set parameters for HTTP/s protocols
        if self.stream_args["stream_info"]["url"].startswith(tuple(["http://", "https://"])):

            try:
                channel_stream_url_headers = self.fhdhr.web.session.head(self.stream_args["stream_info"]["url"]).headers
                self.stream_args["true_content_type"] = channel_stream_url_headers['Content-Type']

            except self.fhdhr.web.exceptions.MissingSchema:
                raise TunerError("806 - Tune Failed")

            except self.fhdhr.web.exceptions.ConnectionError:
                raise TunerError("806 - Tune Failed")

            except KeyError:

                # Set for M3U8
                if self.stream_args["stream_info"]["url"].endswith(tuple([".m3u8", ".m3u"])):
                    self.fhdhr.logger.warning("Stream Headers couldn't be properly determined, defaulting to application/text as content_type.")
                    self.stream_args["true_content_type"] = "application/text"

                else:
                    self.fhdhr.logger.warning("Stream Headers couldn't be properly determined, defaulting to video/mpeg as content_type.")
                    self.stream_args["true_content_type"] = "video/mpeg"

            if self.stream_args["true_content_type"].startswith(tuple(["application/", "text/"])):

                self.stream_args["content_type"] = "video/mpeg"
                if self.stream_args["origin_quality"] != -1:
                    self.stream_args["stream_info"]["url"] = m3u8_quality(self.fhdhr, self.stream_args)

            else:
                self.stream_args["content_type"] = self.stream_args["true_content_type"]

        # Set parameters for Hardware Devices
        elif self.stream_args["stream_info"]["url"].startswith(tuple(["/dev/", "file://dev/"])):
            # TODO some attempt to determine this information properly
            self.stream_args["true_content_type"] = "video/mpeg"

        # Set parameters for file://
        elif self.stream_args["stream_info"]["url"].startswith(tuple(["file://"])):

            # Set for M3U8
            if self.stream_args["stream_info"]["url"].endswith(tuple([".m3u8", ".m3u"])):
                self.stream_args["true_content_type"] = "application/text"

            else:
                # TODO some attempt to determine this information properly
                self.stream_args["true_content_type"] = "video/mpeg"

        # Set parameters for RTP/s protocols
        elif self.stream_args["stream_info"]["url"].startswith(tuple(["rtp://", "rtsp://"])):
            # TODO some attempt to determine this information properly
            self.stream_args["true_content_type"] = "video/mpeg"

        # Set parameters for UDP protocol
        elif self.stream_args["stream_info"]["url"].startswith(tuple(["udp://"])):
            # TODO some attempt to determine this information properly
            self.stream_args["true_content_type"] = "video/mpeg"

        # Set parameters for fallback
        else:
            self.fhdhr.logger.warning("Content Type couldn't be properly determined, defaulting to video/mpeg as content_type.")
            self.stream_args["true_content_type"] = "video/mpeg"

        if self.stream_args["true_content_type"].startswith(tuple(["application/", "text/"])):

            self.stream_args["content_type"] = "video/mpeg"
            if self.stream_args["origin_quality"] != -1:
                self.stream_args["stream_info"]["url"] = m3u8_quality(self.fhdhr, self.stream_args)

        else:
            self.stream_args["content_type"] = self.stream_args["true_content_type"]
