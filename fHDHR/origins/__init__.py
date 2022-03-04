
from fHDHR.tools import checkattr
from .origin import Origin
from .channels.chan_ident import Channel_IDs


class Origins():
    """
    fHDHR Origins system.
    """

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

        self.origins_dict = {}

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

    """Channel Searching"""

    def find_channel_obj(self, chan_searchfor, searchkey=None, origin=None):
        """
        Get a channel_obj
        """
        chan_obj = None

        # Must have a channel to search for
        if not chan_searchfor:
            return None

        # If not origin, but there's only one origin,
        # we can safely make an assumption here
        if not origin and self.count_origin == 1:
            origin = self.first_origin

        # Handling for when origin is provided, which is an optimal situation
        if origin:

            # if the origin is invalid, then so is the channel
            if origin not in self.list_origins:
                return None

            return self.origins_dict[origin].channels.find_channel_obj(chan_searchfor, searchkey)

        # No provided origin makes searching harder, but not impossible
        # this will however select the first possible match, and is not
        # an optimal situation
        else:
            searchkey_matches = []
            for origin in self.list_origins:

                channel_obj = self.origins_dict[origin].channels.find_channel_obj(chan_searchfor, searchkey)
                if channel_obj:
                    searchkey_matches.extend(channel_obj.dict["id"])

            if not len(searchkey_matches):
                return None

            # Grab first matched channel_id and reverse search the origin
            channel_id = searchkey_matches[0]
            origins = [origin for origin in self.list_origins if channel_id in self.origins_dict[origin].channels.list_channel_ids]

            # Hopefully we found an origin
            if not len(origins):
                return None
            origin = origins[0]

            # Channel matched, really shouldn't find more than one
            chan_obj = self.origins_dict[origin].channels.get_channel_object(channel_id)

            return chan_obj

        return chan_obj

    def get_channel_obj(self, keyfind, valfind, origin=None):
        """
        Retrieve channel object by keyfind property.
        """
        # TODO deprecate
        return self.find_channel_obj(valfind, searchkey=keyfind, origin=origin)

    def get_channel_list(self, keyfind, origin=None):
        """
        Get a list of channels by keyfind property.
        """

        if origin:

            return self.origins_dict[origin].channels.create_channel_list(keyfind)

        else:

            matches = []
            for origin in list(self.list.keys()):

                next_match = self.origins_dict[origin].channels.create_channel_list(keyfind)

                if len(next_match):
                    matches.append(next_match)

            return matches[0]

    def get_channels(self, origin=None, forceupdate=False):
        """
        Pull Channels from origin.
        """

        if not origin:
            origins_list = self.list_origins
        elif isinstance(origin, str):
            origins_list = [origin.lower()]
        else:
            origins_list = origin

        return_chan_list = []
        for origin in origins_list:
            chan_list = self.origins_dict[origin].channels.get_channels(forceupdate)
            return_chan_list.extend(chan_list)
        return return_chan_list
