
from fHDHR.tools import checkattr
from .origin import Origin
from .channels.chan_ident import Channel_IDs
from .channels.origin_hunt import Origin_Hunt


class Origins():
    """
    fHDHR Origins system.
    """

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

        self.origins_dict = {}

        self.channels = Origin_Hunt(fhdhr, self)

        self.id_system = Channel_IDs(fhdhr, self)

        self.selfadd_origins()

        self.fhdhr.logger.debug("Giving Packaged non-origin Origin Plugins access to base origin plugin.")
        for plugin_name in list(self.fhdhr.plugins.plugins.keys()):
            plugin = self.fhdhr.plugins.plugins[plugin_name]
            if (plugin.manifest["tagged_mod"] and plugin.manifest["tagged_mod_type"] == "origin"):
                plugin.plugin_utils.origin_obj = self.origins_dict[plugin.manifest["tagged_mod"].lower()]
                plugin.plugin_utils.origin_name = plugin.plugin_utils.origin_obj.name

    @property
    def list_origins(self):
        return [origin_name for origin_name in list(self.origins_dict.keys())]

    @property
    def count_origins(self):
        return len(self.list_origins)

    @property
    def first_origin(self):
        if self.count_origins:
            return self.list_origins[0]
        return None

    def get_origin_obj(self, origin_name):
        if origin_name not in self.list_origins:
            return None
        return self.origins_dict[origin_name]

    def get_origin_conf(self, origin_name):
        conf_dict = {}
        if origin_name not in self.list_origins:
            return conf_dict
        return self.origins_dict[origin_name].get_origin_conf()

    def get_origin_property(self, origin_name, origin_attr):
        if origin_name not in self.list_origins:
            return None
        return self.origins_dict[origin_name].get_origin_property(origin_attr)

    def origin_has_method(self, origin_name, origin_attr):
        if origin_name not in self.list_origins:
            return None
        return self.origins_dict[origin_name].has_method(origin_attr)

    def selfadd_origins(self):
        """
        Import Origins.
        """

        self.fhdhr.logger.info("Detecting and Opening any found origin plugins.")
        for plugin_name in self.fhdhr.plugins.search_by_type("origin"):

            plugin = self.fhdhr.plugins.plugins[plugin_name]
            method = plugin.name.lower()
            self.fhdhr.logger.info("Found Origin: %s" % method)
            self.origins_dict[method] = Origin(self.fhdhr, plugin, self.id_system)

    """Dirty Shortcut area"""

    def __getattr__(self, name):
        """
        Quick and dirty shortcuts. Will only get called for undefined attributes.
        """

        if checkattr(self.channels, name):
            return eval("self.channels.%s" % name)
