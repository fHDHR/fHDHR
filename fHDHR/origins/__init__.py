
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
        self.default_stream_method = self.fhdhr.config.dict["fhdhr"]["default_stream_method"]
        self.default_chanscan_on_start = self.fhdhr.config.dict["fhdhr"]["chanscan_on_start"]

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

                if not hasattr(self.origins_dict[method], 'tuners'):
                    self.origins_dict[method].tuners = self.default_tuners
                    self.fhdhr.logger.debug("%s Origin Does not have a tuners attribute, setting to `%s`" % (method, self.default_tuners))

                if not hasattr(self.origins_dict[method], 'stream_method'):
                    self.origins_dict[method].stream_method = self.default_stream_method
                    self.fhdhr.logger.debug("%s Origin Does not have a stream_method attribute, setting to `%s`" % (method, self.default_stream_method))

                if not hasattr(self.origins_dict[method], 'chanscan_on_start'):
                    self.origins_dict[method].chanscan_on_start = self.default_chanscan_on_start
                    self.fhdhr.logger.debug("%s Origin Does not have a chanscan_on_start attribute, setting to `%s`" % (method, self.default_chanscan_on_start))
