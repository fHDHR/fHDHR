
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
                plugin.plugin_utils.origin = self.origins_dict[plugin.manifest["tagged_mod"].lower()]

    @property
    def list_origins(self):
        return [origin for origin in list(self.origins_dict.keys())]

    @property
    def count_origins(self):
        return len(self.list_origins)

    @property
    def first_origin(self):
        return self.list_origins[0]

    def get_origin(self, origin):
        if origin not in self.list_origins:
            return None
        return self.origins_dict[origin]

    def get_origin_conf(self, origin):
        conf_dict = {}
        if origin not in self.list_origins:
            return conf_dict
        for conf_key in list(self.origins_dict[origin].default_settings.keys()):
            conf_dict[conf_key] = self.get_origin_property(origin, conf_key)
        return conf_dict

    def get_origin_property(self, origin, origin_attr):
        if origin not in self.list_origins:
            return None
        if checkattr(self.origins_dict[origin], origin_attr):
            return eval("self.origins_dict[origin].%s" % origin_attr)
        return None

    def origin_has_method(self, origin, origin_attr):
        if origin not in self.list_origins:
            return None
        return self.origins_dict[origin].has_method(origin_attr)

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
