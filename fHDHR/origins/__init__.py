
import fHDHR.exceptions


class Origin_StandIN():
    """
    A standin for Origins that fail to setup properly.
    """

    def __init__(self):
        self.setup_success = False

    def get_channels(self):
        return []

    def get_channel_stream(self, chandict, stream_args):
        return None


class Origins():
    """
    fHDHR Origins system.
    """

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

        self.default_tuners = self.fhdhr.config.dict["fhdhr"]["default_tuners"]
        self.default_chanscan_on_start = self.fhdhr.config.dict["fhdhr"]["chanscan_on_start"]
        self.default_chanscan_interval = self.fhdhr.config.dict["fhdhr"]["chanscan_interval"]

        self.default_stream_method = self.fhdhr.config.dict["fhdhr"]["default_stream_method"]
        self.default_origin_quality = self.fhdhr.config.dict["streaming"]["origin_quality"]
        self.default_transcode_quality = self.fhdhr.config.dict["streaming"]["transcode_quality"]
        self.default_bytes_per_read = self.fhdhr.config.dict["streaming"]["bytes_per_read"]
        self.default_buffer_size = self.fhdhr.config.dict["streaming"]["buffer_size"]
        self.default_stream_restore_attempts = self.fhdhr.config.dict["streaming"]["stream_restore_attempts"]

        self.origins_dict = {}
        self.origin_selfadd()

        self.fhdhr.logger.debug("Giving Packaged non-origin Origin Plugins access to base origin plugin.")

        for plugin_name in list(self.fhdhr.plugins.plugins.keys()):

            if self.fhdhr.plugins.plugins[plugin_name].manifest["tagged_mod"] and self.fhdhr.plugins.plugins[plugin_name].manifest["tagged_mod_type"] == "origin":
                self.fhdhr.plugins.plugins[plugin_name].plugin_utils.origin = self.origins_dict[self.fhdhr.plugins.plugins[plugin_name].manifest["tagged_mod"].lower()]

    @property
    def valid_origins(self):
        """
        Generate a list of valid origins.
        """

        return [origin for origin in list(self.origins_dict.keys())]

    def origin_selfadd(self):
        """
        Import Origins.
        """

        self.fhdhr.logger.info("Detecting and Opening any found origin plugins.")
        for plugin_name in list(self.fhdhr.plugins.plugins.keys()):

            if self.fhdhr.plugins.plugins[plugin_name].type == "origin":

                method = self.fhdhr.plugins.plugins[plugin_name].name.lower()
                self.fhdhr.logger.info("Found Origin: %s" % method)

                try:
                    plugin_utils = self.fhdhr.plugins.plugins[plugin_name].plugin_utils
                    self.origins_dict[method] = self.fhdhr.plugins.plugins[plugin_name].Plugin_OBJ(plugin_utils)
                    self.fhdhr.logger.info("%s Origin Setup Success" % method)
                    self.origins_dict[method].setup_success = True

                except fHDHR.exceptions.OriginSetupError as e:
                    self.fhdhr.logger.error("%s Origin Setup Failed: %s" % (method, e))
                    self.origins_dict[method] = Origin_StandIN()

                except Exception as e:
                    self.fhdhr.logger.error("%s Origin Setup Failed: %s" % (method, e))
                    self.origins_dict[method] = Origin_StandIN()

                if not hasattr(self.origins_dict[method], 'tuners'):
                    tuners = self.default_tuners
                    if method in list(self.fhdhr.config.dict.keys()):
                        if "tuners" in list(self.fhdhr.config.dict[method].keys()):
                            tuners = self.fhdhr.config.dict[method]["tuners"]
                    self.fhdhr.logger.debug("Setting %s tuners attribute to: %s" % (method, tuners))
                    self.origins_dict[method].tuners = tuners

                if not hasattr(self.origins_dict[method], 'chanscan_on_start'):
                    chanscan_on_start = self.default_chanscan_on_start
                    if method in list(self.fhdhr.config.dict.keys()):
                        if "chanscan_on_start" in list(self.fhdhr.config.dict[method].keys()):
                            chanscan_on_start = self.fhdhr.config.dict[method]["chanscan_on_start"]
                    self.fhdhr.logger.debug("Setting %s chanscan_on_start attribute to: %s" % (method, chanscan_on_start))
                    self.origins_dict[method].chanscan_on_start = chanscan_on_start

                if not hasattr(self.origins_dict[method], 'chanscan_interval'):
                    chanscan_interval = self.default_chanscan_interval
                    if method in list(self.fhdhr.config.dict.keys()):
                        if "chanscan_interval" in list(self.fhdhr.config.dict[method].keys()):
                            chanscan_interval = self.fhdhr.config.dict[method]["chanscan_interval"]
                    self.fhdhr.logger.debug("Setting %s chanscan_interval attribute to: %s" % (method, chanscan_interval))
                    self.origins_dict[method].chanscan_interval = chanscan_interval

                if not hasattr(self.origins_dict[method], 'stream_method'):
                    stream_method = self.default_stream_method
                    if method in list(self.fhdhr.config.dict.keys()):
                        if "stream_method" in list(self.fhdhr.config.dict[method].keys()):
                            stream_method = self.fhdhr.config.dict[method]["stream_method"]
                    self.fhdhr.logger.debug("Setting %s stream_method attribute to: %s" % (method, stream_method))
                    self.origins_dict[method].stream_method = stream_method

                if not hasattr(self.origins_dict[method], 'origin_quality'):
                    origin_quality = self.default_origin_quality
                    if method in list(self.fhdhr.config.dict.keys()):
                        if "origin_quality" in list(self.fhdhr.config.dict[method].keys()):
                            origin_quality = self.fhdhr.config.dict[method]["origin_quality"]
                    self.fhdhr.logger.debug("Setting %s origin_quality attribute to: %s" % (method, origin_quality))
                    self.origins_dict[method].origin_quality = origin_quality

                if not hasattr(self.origins_dict[method], 'transcode_quality'):
                    transcode_quality = self.default_transcode_quality
                    if method in list(self.fhdhr.config.dict.keys()):
                        if "transcode_quality" in list(self.fhdhr.config.dict[method].keys()):
                            transcode_quality = self.fhdhr.config.dict[method]["transcode_quality"]
                    self.fhdhr.logger.debug("Setting %s transcode_quality attribute to: %s" % (method, transcode_quality))
                    self.origins_dict[method].transcode_quality = transcode_quality

                if not hasattr(self.origins_dict[method], 'bytes_per_read'):
                    bytes_per_read = self.default_bytes_per_read
                    if method in list(self.fhdhr.config.dict.keys()):
                        if "bytes_per_read" in list(self.fhdhr.config.dict[method].keys()):
                            bytes_per_read = self.fhdhr.config.dict[method]["bytes_per_read"]
                    self.fhdhr.logger.debug("Setting %s bytes_per_read attribute to: %s" % (method, bytes_per_read))
                    self.origins_dict[method].bytes_per_read = bytes_per_read

                if not hasattr(self.origins_dict[method], 'buffer_size'):
                    buffer_size = self.default_buffer_size
                    if method in list(self.fhdhr.config.dict.keys()):
                        if "buffer_size" in list(self.fhdhr.config.dict[method].keys()):
                            buffer_size = self.fhdhr.config.dict[method]["buffer_size"]
                    self.fhdhr.logger.debug("Setting %s buffer_size attribute to: %s" % (method, buffer_size))
                    self.origins_dict[method].buffer_size = buffer_size

                if not hasattr(self.origins_dict[method], 'stream_restore_attempts'):
                    stream_restore_attempts = self.default_stream_restore_attempts
                    if method in list(self.fhdhr.config.dict.keys()):
                        if "stream_restore_attempts" in list(self.fhdhr.config.dict[method].keys()):
                            stream_restore_attempts = self.fhdhr.config.dict[method]["stream_restore_attempts"]
                    self.fhdhr.logger.debug("Setting %s stream_restore_attempts attribute to: %s" % (method, stream_restore_attempts))
                    self.origins_dict[method].stream_restore_attempts = stream_restore_attempts
