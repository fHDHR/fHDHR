
from .origin import Origin


class Origin_StandIN():
    """
    A standin for Origins that fail to setup properly.
    """

    def __init__(self, plugin_utils):
        self.setup_success = False
        self.plugin_utils = plugin_utils

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

        self.origins_dict = {}
        self.origin_selfadd()

        self.fhdhr.logger.debug("Giving Packaged non-origin Origin Plugins access to base origin plugin.")

        for plugin_name in list(self.fhdhr.plugins.plugins.keys()):
            plugin = self.fhdhr.plugins.plugins[plugin_name]

            if (plugin.manifest["tagged_mod"] and plugin.manifest["tagged_mod_type"] == "origin"):
                plugin.plugin_utils.origin = self.origins_dict[plugin.manifest["tagged_mod"].lower()]

    @property
    def valid_origins(self):
        """Generate a list of valid origins."""
        return [origin for origin in list(self.origins_dict.keys())]

    def origin_selfadd(self):
        """
        Import Origins.
        """

        self.fhdhr.logger.info("Detecting and Opening any found origin plugins.")
        for plugin_name in self.fhdhr.plugins.search_by_type("origin"):

            plugin = self.fhdhr.plugins.plugins[plugin_name]
            method = plugin.name.lower()
            self.fhdhr.logger.info("Found Origin: %s" % method)
            self.origins_dict[method] = Origin(self.fhdhr, plugin)
