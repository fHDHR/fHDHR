
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
            # "reconnect": {"section": "streaming", "option": "reconnect"}
            }

        # Create Default Config Values and Descriptions for Streaming
        self.default_settings = self.fhdhr.config.get_plugin_defaults(self.default_settings)

        self.alt_stream_handlers = {}

        self.alt_stream_methods_selfadd()

    def alt_stream_methods_selfadd(self):
        """
        Import stream methods.
        """

        self.fhdhr.logger.info("Detecting and Opening any found Stream Method plugins.")
        for plugin_name in list(self.fhdhr.plugins.plugins.keys()):

            if self.fhdhr.plugins.plugins[plugin_name].type == "alt_stream":
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

            for default_setting in list(self.default_settings.keys()):

                # Set Origin attributes if missing
                if not hasattr(self.alt_stream_handlers[stream_method], default_setting):
                    self.fhdhr.logger.debug("Setting %s %s attribute to: %s" % (stream_method, default_setting, self.fhdhr.config.dict[stream_method][default_setting]))
                    setattr(self.alt_stream_handlers[stream_method], default_setting, self.fhdhr.config.dict[stream_method][default_setting])

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
        return Stream_OBJ(self.fhdhr, self.device, self.origins, request, session, chan_obj, stream_args)

    def setup_stream(self, request, session):
        """
        This Stream Setup focuses on verifying api endpoint parameters
        prior to instantiating the Stream_OBJ Object
        """

        stream_args = {}

        # Get Channel object from request
        chan_obj, response_dict = self.parse_channel_args_for_chan_obj(request)
        if not chan_obj:
            return None, None, response_dict
        stream_args.update({"channel": chan_obj.number,
                            "channel_name": chan_obj.name,
                            "channel_callsign": chan_obj.callsign,
                            "origin": chan_obj.origin})

        # Get Streaming args from request
        streaming_args, response_dict = self.parse_stream_args(request, chan_obj.origin)
        if not len(list(stream_args.keys())):
            return None, None, response_dict
        stream_args.update(streaming_args)

        request_dict = self.parse_request_for_client_info(request, session)
        stream_args.update(request_dict)

        settings_dict = self.parse_settings_for_stream(chan_obj.origin)
        stream_args.update(settings_dict)

        stream_obj = self.get_stream_obj(chan_obj, request, session, stream_args)

        return stream_obj, stream_args, None

    def parse_channel_args_for_chan_obj(self, request):
        """Use the passed `request` information to grab the correct channel object"""

        chan_obj = None
        response_dict = None

        origin = request.args.get('origin', default=None, type=str)
        channel_number = request.args.get('channel', None, type=str)

        # Cannot continue if not provided a channel
        if not channel_number:
            return chan_obj, {"message": "Not Found", "status_code": 404, "headers": "801 - Missing Channel"}

        chan_obj = self.device.channels.get_channel_obj_search(origin, channel_number)

        if not chan_obj:
            if not origin:
                response_dict = {"message": "Not Found", "status_code": 404, "headers": "801 - Unknown Origin"}
            else:
                response_dict = {"message": "Not Found", "status_code": 404, "headers": "801 - Unknown Channel"}

        elif not chan_obj.dict["enabled"]:
            response_dict = {"message": "Service Unavailable", "status_code": 503, "headers": "806 - Tune Failed: Channel Disabled"}

        return chan_obj, response_dict

    def parse_stream_args(self, request, origin):
        """Use the passed `request` information to grab the given stream arguments"""

        stream_args = {}

        response_dict = None

        stream_method = request.args.get('stream_method', default=self.origins.origins_dict[origin].stream_method, type=str)
        if stream_method not in self.streaming_methods:
            response_dict = {"message": "Not Found", "status_code": 503, "headers": "806 - Tune Failed: Invalid Stream Method"}
            return stream_args, response_dict

        duration = request.args.get('duration', default=0, type=int)

        transcode_quality = request.args.get('transcode', default=self.fhdhr.origins.origins_dict[origin].transcode_quality, type=str)
        valid_transcode_types = [None, "heavy", "mobile", "internet720", "internet480", "internet360", "internet240"]
        if transcode_quality not in valid_transcode_types:
            response_dict = {"message": "Not Found", "status_code": 503, "headers": "802 - Unknown Transcode Profile"}
            return stream_args, response_dict

        tuner_number = request.args.get('tuner', default=None, type=str)

        stream_args = {
                        "origin": origin,
                        "method": stream_method,
                        "duration": duration,
                        "tuner_number": tuner_number,
                        "transcode_quality": transcode_quality,
                        }

        return stream_args, response_dict

    def parse_request_for_client_info(self, request, session):
        """Use the passed `request` information to grab the information regarding the client"""
        request_dict = {
                        "accessed": request.args.get('accessed', default=request.url, type=str),
                        "base_url": request.url_root[:-1],
                        "client": request.remote_addr,
                        "client_id": session["session_id"]
                        }
        return request_dict

    def parse_settings_for_stream(self, origin):
        """Pull Origin specific settings for the stream"""
        settings_dict = {
                        "origin_quality": self.origins.origins_dict[origin].origin_quality,
                        "bytes_per_read": self.origins.origins_dict[origin].bytes_per_read,
                        "buffer_size": self.origins.origins_dict[origin].buffer_size,
                        "stream_restore_attempts": self.origins.origins_dict[origin].stream_restore_attempts,
                        }
        return settings_dict
