

class Origin_Hunt():
    """
    fHDHR Origin_Hunt system.
    """

    def __init__(self, fhdhr, origins):
        self.fhdhr = fhdhr
        self.origins = origins

    """Channel Searching"""

    def run_schedule_scan(self, origin_name=None):

        # If not origin, but there's only one origin,
        # we can safely make an assumption here
        if not origin_name and self.origins.count_origin == 1:
            origin_name = self.origins.first_origin

        # Handling for when origin is provided, which is an optimal situation
        if origin_name:

            # if the origin is invalid, then so is the channel
            if origin_name not in self.origins.list_origins:
                return None

            self.origins.origins_dict[origin_name].channels.run_schedule_scan()

        else:
            for origin_name in self.origins.list_origins:
                self.origins.origins_dict[origin_name].channels.run_schedule_scan()

    def find_channel_obj(self, chan_searchfor, searchkey=None, origin_name=None):
        """
        Get a channel_obj
        """
        chan_obj = None

        # Must have a channel to search for
        if not chan_searchfor:
            return None

        # If not origin_name, but there's only one origin_name,
        # we can safely make an assumption here
        if not origin_name and self.origins.count_origin == 1:
            origin_name = self.origins.first_origin

        # Handling for when origin_name is provided, which is an optimal situation
        if origin_name:

            # if the origin_name is invalid, then so is the channel
            if origin_name not in self.origins.list_origins:
                return None

            return self.origins.origins_dict[origin_name].channels.find_channel_obj(chan_searchfor, searchkey)

        # No provided origin_name makes searching harder, but not impossible
        # this will however select the first possible match, and is not
        # an optimal situation
        else:
            searchkey_matches = []
            for origin_name in self.origins.list_origins:

                channel_obj = self.origins.origins_dict[origin_name].channels.find_channel_obj(chan_searchfor, searchkey)
                if channel_obj:
                    searchkey_matches.extend(channel_obj.dict["id"])

            if not len(searchkey_matches):
                return None

            # Grab first matched channel_id and reverse search the origin_name
            channel_id = searchkey_matches[0]
            origins = [origin_name for origin_name in self.origins.list_origins if channel_id in self.origins.origins_dict[origin_name].channels.list_channel_ids]

            # Hopefully we found an origin
            if not len(origins):
                return None
            origin_name = origins[0]

            # Channel matched, really shouldn't find more than one
            chan_obj = self.origins.origins_dict[origin_name].channels.get_channel_obj(channel_id)

            return chan_obj

        return chan_obj

    def get_channel_obj(self, keyfind, valfind, origin_name=None):
        """
        Retrieve channel object by keyfind property.
        """
        # TODO deprecate
        return self.find_channel_obj(valfind, searchkey=keyfind, origin_name=origin_name)

    def get_channel_list(self, keyfind, origin_name=None):
        """
        Get a list of channels by keyfind property.
        """

        if origin_name:

            return self.origins.origins_dict[origin_name].channels.create_channel_list(keyfind)

        else:

            matches = []
            for origin_name in self.origins.list_origins:

                next_match = self.origins.origins_dict[origin_name].channels.create_channel_list(keyfind)

                if len(next_match):
                    matches.append(next_match)

            return matches[0]

    def get_channels(self, origin_name=None, forceupdate=False):
        """
        Pull Channels from origin_name.
        """

        if not origin_name:
            origins_list = self.origins.list_origins
        elif isinstance(origin_name, str):
            origins_list = [origin_name.lower()]
        else:
            origins_list = origin_name

        return_chan_list = []
        for origin_name in origins_list:
            chan_list = self.origins.origins_dict[origin_name].channels.get_channels(forceupdate)
            return_chan_list.extend(chan_list)
        return return_chan_list
