
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

        self.origins_dict = {}
        self.origin_selfadd()
        for plugin_name in list(self.fhdhr.plugins.plugins.keys()):
            if self.fhdhr.plugins.plugins[plugin_name].manifest["tagged_mod"] and self.fhdhr.plugins.plugins[plugin_name].manifest["tagged_mod_type"] == "origin":
                self.fhdhr.plugins.plugins[plugin_name].plugin_utils.origin = self.origins_dict[self.fhdhr.plugins.plugins[plugin_name].manifest["tagged_mod"].lower()]

    @property
    def valid_origins(self):
        return [origin for origin in list(self.origins_dict.keys())]

    def origin_selfadd(self):
        for plugin_name in list(self.fhdhr.plugins.plugins.keys()):
            if self.fhdhr.plugins.plugins[plugin_name].type == "origin":
                method = self.fhdhr.plugins.plugins[plugin_name].name.lower()
                try:
                    plugin_utils = self.fhdhr.plugins.plugins[plugin_name].plugin_utils
                    self.origins_dict[method] = self.fhdhr.plugins.plugins[plugin_name].Plugin_OBJ(plugin_utils)
                    self.fhdhr.logger.info("%s Setup Success" % method)
                    self.origins_dict[method].setup_success = True
                except fHDHR.exceptions.OriginSetupError as e:
                    self.fhdhr.logger.error(e)
                    self.origins_dict[method] = Origin_StandIN()

                if not hasattr(self.origins_dict[method], 'tuners'):
                    self.origins_dict[method].tuners = 4
