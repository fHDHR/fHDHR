
from.stream_obj import Stream_OBJ


class StreamManager():
    """
    Stream Management
    """

    def __init__(self, fhdhr, device, origins):
        self.fhdhr = fhdhr
        self.device = device
        self.origins = origins
        self.fhdhr.logger.info("Initializing Streaming Manager system")

        # Gather Default settings to pass to origins later
        self.default_settings = {
            }

        # Create Default Config Values and Descriptions for Streaming
        self.default_settings = self.fhdhr.config.get_plugin_defaults(self.default_settings)

        self.alt_stream_handlers = {}

        self.selfadd_plugins()

    def selfadd_plugins(self):
        """
        Import stream methods.
        """

        self.fhdhr.logger.info("Detecting and Opening any found Stream Method plugins.")
        for plugin_name in self.fhdhr.plugins.search_by_type("alt_stream"):

            method = self.fhdhr.plugins.plugins[plugin_name].name
            self.alt_stream_handlers[method] = self.fhdhr.plugins.plugins[plugin_name]

        for stream_method in list(self.alt_stream_handlers.keys()):

            # Create config section in config system
            if stream_method not in list(self.fhdhr.config.dict.keys()):
                self.fhdhr.config.dict[stream_method] = {}

            # Create config defaults section in config system
            if stream_method not in list(self.fhdhr.config.conf_default.keys()):
                self.fhdhr.config.conf_default[stream_method] = {}

            # Set config defaults for method
            self.fhdhr.config.set_plugin_defaults(stream_method, self.default_settings)

    @property
    def streaming_methods(self):
        """
        List valid streaming methods.
        """
        streaming_methods = list(self.alt_stream_handlers.keys())
        streaming_methods.extend(["direct", "passthrough"])
        return streaming_methods

    def get_stream_obj(self, chan_obj, request, session, stream_args):
        self.fhdhr.logger.debug("Instantiating Stream_OBJ Object")
        return Stream_OBJ(self.fhdhr, self.device, self.origins, self.alt_stream_handlers, request, session, chan_obj, stream_args)

    def setup_stream(self, request, session):
        """
        This Stream Setup focuses on verifying api endpoint parameters
        prior to instantiating the Stream_OBJ Object
        """

        self.fhdhr.logger.debug("Setting up stream")

        stream_args = {}

        # Get Channel object from request
        chan_obj, response_dict = self.parse_channel_args_for_chan_obj(request)
        if not chan_obj:
            return None, None, response_dict
        stream_args.update({"channel": chan_obj.number,
                            "channel_name": chan_obj.name,
                            "channel_callsign": chan_obj.callsign,
                            "origin_name": chan_obj.origin_name})

        # Get Streaming args from request
        streaming_args, response_dict = self.parse_stream_args(request, chan_obj.origin_name)
        if not len(list(stream_args.keys())):
            return None, None, response_dict
        stream_args.update(streaming_args)

        request_dict = self.parse_request_for_client_info(request, session)
        stream_args.update(request_dict)

        settings_dict = self.parse_settings_for_stream(chan_obj.origin_name)
        stream_args.update(settings_dict)

        stream_obj = self.get_stream_obj(chan_obj, request, session, stream_args)

        return stream_obj, stream_args, None

    def parse_channel_args_for_chan_obj(self, request):
        """Use the passed `request` information to grab the correct channel object"""

        self.fhdhr.logger.debug("Parsing URL request arguments from client for channel information.")

        chan_obj = None
        response_dict = None

        origin_name = request.args.get('origin', default=None, type=str)
        if origin_name:
            self.fhdhr.logger.debug("Client has selected %s" % origin_name)
        else:
            self.fhdhr.logger.warning("Clien did not request a specific origin.")

        channel_number = request.args.get('channel', None, type=str)
        if channel_number:
            self.fhdhr.logger.debug("Client requested the channel %s" % channel_number)
        else:
            self.fhdhr.logger.error("Client failed to request a channel.")

        # Cannot continue if not provided a channel
        if not channel_number:
            return chan_obj, {"message": "Not Found", "status_code": 404, "headers": "801 - Missing Channel"}

        chan_obj = self.fhdhr.origins.origins_dict[origin_name].channels.find_channel_obj(channel_number, searchkey=None)
        if chan_obj:
            self.fhdhr.logger.debug("Channel information has been determined as: Channel=%s Origin=%s" % (chan_obj.number, chan_obj.origin_name))
        else:
            self.fhdhr.logger.error("Could not determine Channel.")

        if not chan_obj:
            if not origin_name:
                response_dict = {"message": "Not Found", "status_code": 404, "headers": "801 - Unknown Origin"}
            else:
                response_dict = {"message": "Not Found", "status_code": 404, "headers": "801 - Unknown Channel"}

        elif not chan_obj.dict["enabled"]:
            response_dict = {"message": "Service Unavailable", "status_code": 503, "headers": "806 - Tune Failed: Channel Disabled"}

        return chan_obj, response_dict

    def parse_stream_args(self, request, origin_name):
        """Use the passed `request` information to grab the given stream arguments"""

        stream_args = {}

        self.fhdhr.logger.debug("Parsing URL arguments for stream handling.")

        response_dict = None

        stream_method = request.args.get('stream_method', default=None, type=str)
        if stream_method:
            self.fhdhr.logger.debug("Client has specifically requested the %s stream method." % stream_method)
        else:
            stream_method = self.origins.get_origin_property(origin_name, "stream_method")
            self.fhdhr.logger.debug("Client did not select a stream method. Defaulting to origin %s setting of %s" % (origin_name, stream_method))
        if stream_method not in self.streaming_methods:
            response_dict = {"message": "Not Found", "status_code": 503, "headers": "806 - Tune Failed: Invalid Stream Method"}
            return stream_args, response_dict

        duration = request.args.get('duration', default=0, type=int)
        if duration:
            self.fhdhr.logger.debug("Client requested duration of %s" % self.fhdhr.time.humanized_time(duration))
        else:
            self.fhdhr.logger.debug("Client did not specify a duration to end the stream, stream will run indefinately.")

        transcode_quality = request.args.get('transcode', default=None, type=str)
        if transcode_quality:
            self.fhdhr.logger.debug("Client requested transcoding to %s quality." % transcode_quality)
        else:
            transcode_quality = self.fhdhr.origins.get_origin_property(origin_name, "transcode_quality")
            self.fhdhr.logger.debug("Client did not select a transcode quality. Defaulting to origin %s setting of %s" % (origin_name, transcode_quality))

        valid_transcode_types = [None, "heavy", "mobile", "internet720", "internet480", "internet360", "internet240"]
        if transcode_quality not in valid_transcode_types:
            response_dict = {"message": "Not Found", "status_code": 503, "headers": "802 - Unknown Transcode Profile"}
            return stream_args, response_dict

        tuner_number = request.args.get('tuner', default=None, type=str)
        if tuner_number:
            self.fhdhr.logger.debug("Client has specified utilization of %s tuner number %s." % (origin_name, tuner_number))
        else:
            self.fhdhr.logger.debug("Client did not specify a tuner number, automatic selection enabled.")

        stream_args = {
                        "origin_name": origin_name,
                        "method": stream_method,
                        "duration": duration,
                        "tuner_number": tuner_number,
                        "transcode_quality": transcode_quality,
                        }

        return stream_args, response_dict

    def parse_request_for_client_info(self, request, session):
        """Use the passed `request` information to grab the information regarding the client"""
        self.fhdhr.logger.debug("Logging information regarding how the client has accessed the stream.")
        request_dict = {
                        "accessed": request.args.get('accessed', default=request.url, type=str),
                        "base_url": request.url_root[:-1],
                        "client": request.remote_addr,
                        "client_id": session["session_id"]
                        }
        return request_dict

    def parse_settings_for_stream(self, origin_name):
        """Pull Origin specific settings for the stream"""
        settings_dict = {
                        "origin_quality": self.origins.get_origin_property(origin_name, "origin_quality"),
                        "bytes_per_read": self.origins.get_origin_property(origin_name, "bytes_per_read"),
                        "buffer_size": self.origins.get_origin_property(origin_name, "buffer_size"),
                        "stream_restore_attempts": self.origins.get_origin_property(origin_name, "stream_restore_attempts"),
                        }
        stream_settings_string = "Pulling default settings for %s regarding stream handling:"
        for streamkey in list(settings_dict.keys()):
            stream_settings_string += " %s=%s" % (streamkey, settings_dict[streamkey])
        self.fhdhr.logger.debug(stream_settings_string)
        return settings_dict
