

class Origin_Hunt():
    """
    fHDHR Origin_Hunt system.
    """

    def __init__(self, fhdhr, origins):
        self.fhdhr = fhdhr
        self.origins = origins

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
        if not origin and self.origins.count_origin == 1:
            origin = self.origins.first_origin

        # Handling for when origin is provided, which is an optimal situation
        if origin:

            # if the origin is invalid, then so is the channel
            if origin not in self.origins.list_origins:
                return None

            return self.origins.origins_dict[origin].channels.find_channel_obj(chan_searchfor, searchkey)

        # No provided origin makes searching harder, but not impossible
        # this will however select the first possible match, and is not
        # an optimal situation
        else:
            searchkey_matches = []
            for origin in self.origins.list_origins:

                channel_obj = self.origins.origins_dict[origin].channels.find_channel_obj(chan_searchfor, searchkey)
                if channel_obj:
                    searchkey_matches.extend(channel_obj.dict["id"])

            if not len(searchkey_matches):
                return None

            # Grab first matched channel_id and reverse search the origin
            channel_id = searchkey_matches[0]
            origins = [origin for origin in self.origins.list_origins if channel_id in self.origins.origins_dict[origin].channels.list_channel_ids]

            # Hopefully we found an origin
            if not len(origins):
                return None
            origin = origins[0]

            # Channel matched, really shouldn't find more than one
            chan_obj = self.origins.origins_dict[origin].channels.get_channel_object(channel_id)

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

            return self.origins.origins_dict[origin].channels.create_channel_list(keyfind)

        else:

            matches = []
            for origin in self.origins.list_origins:

                next_match = self.origins.origins_dict[origin].channels.create_channel_list(keyfind)

                if len(next_match):
                    matches.append(next_match)

            return matches[0]

    def get_channels(self, origin=None, forceupdate=False):
        """
        Pull Channels from origin.
        """

        if not origin:
            origins_list = self.origins.list_origins
        elif isinstance(origin, str):
            origins_list = [origin.lower()]
        else:
            origins_list = origin

        return_chan_list = []
        for origin in origins_list:
            chan_list = self.origins.origins_dict[origin].channels.get_channels(forceupdate)
            return_chan_list.extend(chan_list)
        return return_chan_list
