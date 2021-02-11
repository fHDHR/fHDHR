
import fHDHR.exceptions


class Origin_StandIN():
    def __init__(self):
        self.setup_success = False

    def get_channels(self):
        return []

    def get_channel_stream(self, chandict, stream_args):
        return None


class Origins():

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

        self.default_tuners = 4
        self.default_stream_method = None

        self.origins_dict = {}
        self.origin_selfadd()
        self.fhdhr.logger.debug("Giving Packaged non-origin Origin Plugins access to base origin plugin.")
        for plugin_name in list(self.fhdhr.plugins.plugins.keys()):
            if self.fhdhr.plugins.plugins[plugin_name].manifest["tagged_mod"] and self.fhdhr.plugins.plugins[plugin_name].manifest["tagged_mod_type"] == "origin":
                self.fhdhr.plugins.plugins[plugin_name].plugin_utils.origin = self.origins_dict[self.fhdhr.plugins.plugins[plugin_name].manifest["tagged_mod"].lower()]

    @property
    def valid_origins(self):
        return [origin for origin in list(self.origins_dict.keys())]

    def origin_selfadd(self):
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
                    self.fhdhr.logger.error("%s Origin Setup Success: %s" % (method, e))
                    self.origins_dict[method] = Origin_StandIN()

                if not hasattr(self.origins_dict[method], 'tuners'):
                    self.origins_dict[method].tuners = 4
                    self.fhdhr.logger.debug("%s Origin Does not have a tuners attribute, setting to `%s`" % self.default_tuners)

                if not hasattr(self.origins_dict[method], 'stream_method'):
                    self.origins_dict[method].stream_method = None
                    self.fhdhr.logger.debug("%s Origin Does not have a stream_method attribute, setting to `%s`" % self.default_stream_method)
