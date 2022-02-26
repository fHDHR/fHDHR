import time

from fHDHR.tools import humanized_time

from .channel import Channel
from .chan_ident import Channel_IDs


class Channels():
    """
    fHDHR Channels system
    """

    def __init__(self, fhdhr, origins):
        self.fhdhr = fhdhr
        self.fhdhr.logger.info("Initializing Channels system")

        self.origins = origins

        self.id_system = Channel_IDs(fhdhr, origins)

        self.list = {}
        for origin in list(self.origins.origins_dict.keys()):
            self.list[origin] = {}

        self.get_db_channels()

        self.channel_update_url = "/api/channels?method=scan"

        for origin in list(self.list.keys()):
            chanscan_interval = self.origins.origins_dict[origin].chanscan_interval
            if chanscan_interval:
                self.fhdhr.scheduler.every(chanscan_interval).seconds.do(
                    self.fhdhr.scheduler.job_wrapper(self.get_channels), origin=origin, forceupdate=True).tag("%s Channel Scan" % origin)

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
        if not origin and len(list(self.list.keys())) == 1:
            origin = list(self.list.keys())[0]

        # Handling for when origin is provided, which is an optimal situation
        if origin:

            # if the origin is invalid, then so is the channel
            if origin not in self.origins.valid_origins:
                return None

            # Get a list of dict for all channels in origin
            origin_channels_dict_list = [self.list[origin][channel_id].dict for channel_id in list(self.list[origin].keys())]

            # If a searchkey is provided, this can be helpful for identifying a channel easier
            if searchkey:

                # search for origin channel by searchkey
                if searchkey != "number":
                    origin_channel_searchkey_matches = [channel_id for channel_id in [channel["id"] for channel in origin_channels_dict_list]
                                                        if searchkey in list(self.list[origin][channel_id].dict.keys())
                                                        and self.list[origin][channel_id].dict[searchkey] == chan_searchfor]
                # Searching by number is unique as the @property combines number and subnumber
                else:
                    origin_channel_searchkey_matches = [channel_id for channel_id in [channel["id"] for channel in origin_channels_dict_list]
                                                        if self.list[origin][channel_id].number == chan_searchfor]

                # searchkey produced no results
                if not len(origin_channel_searchkey_matches):
                    return None

                # Channel matched, really shouldn't find more than one
                channel_id = origin_channel_searchkey_matches[0]
                chan_obj = self.list[origin][channel_id]

                return chan_obj

            else:

                # attempt searching by ID and then number
                searchkey_matches = []
                for searchkey in ["id", "number", "name", "callsign"
                                  "origin_id", "origin_number", "origin_name", "origin_callsign"]:

                    # search for origin channel by searchkey
                    if searchkey != "number":
                        origin_channel_searchkey_matches = [channel_id for channel_id in [channel["id"] for channel in origin_channels_dict_list]
                                                            if searchkey in list(self.list[origin][channel_id].dict.keys())
                                                            and self.list[origin][channel_id].dict[searchkey] == chan_searchfor]
                    # Searching by number is unique as the @property combines number and subnumber
                    else:
                        origin_channel_searchkey_matches = [channel_id for channel_id in [channel["id"] for channel in origin_channels_dict_list]
                                                            if self.list[origin][channel_id].number == chan_searchfor]

                    # Append matches to list
                    searchkey_matches.extend(origin_channel_searchkey_matches)

                # searchkey produced no results
                if not len(searchkey_matches):
                    return None

                # Channel matched, really shouldn't find more than one
                channel_id = searchkey_matches[0]
                chan_obj = self.list[origin][channel_id]

                return chan_obj

        # No provided origin makes searching harder, but not impossible
        # this will however select the first possible match, and is not
        # an optimal situation
        else:
            searchkey_matches = []
            for origin in list(self.list.keys()):

                # If a searchkey is provided, this can be helpful for identifying a channel easier
                if searchkey:

                    # Get a list of dict for all channels in origin
                    origin_channels_dict_list = [self.list[origin][channel_id].dict for channel_id in list(self.list[origin].keys())]

                    # search for origin channel by searchkey
                    if searchkey != "number":
                        origin_channel_searchkey_matches = [channel_id for channel_id in [channel["id"] for channel in origin_channels_dict_list]
                                                            if searchkey in list(self.list[origin][channel_id].dict.keys())
                                                            and self.list[origin][channel_id].dict[searchkey] == chan_searchfor]
                    # Searching by number is unique as the @property combines number and subnumber
                    else:
                        origin_channel_searchkey_matches = [channel_id for channel_id in [channel["id"] for channel in origin_channels_dict_list]
                                                            if self.list[origin][channel_id].number == chan_searchfor]

                    # Append matches to list
                    searchkey_matches.extend(origin_channel_searchkey_matches)

                # No searchkey, no origin
                # This is a desperate attempt at getting this channel object, if it exists
                else:

                    for searchkey in ["id", "number", "name", "callsign"
                                      "origin_id", "origin_number", "origin_name", "origin_callsign"]:

                        # search for origin channel by searchkey
                        if searchkey != "number":
                            origin_channel_searchkey_matches = [channel_id for channel_id in [channel["id"] for channel in origin_channels_dict_list]
                                                                if searchkey in list(self.list[origin][channel_id].dict.keys())
                                                                and self.list[origin][channel_id].dict[searchkey] == chan_searchfor]
                        # Searching by number is unique as the @property combines number and subnumber
                        else:
                            origin_channel_searchkey_matches = [channel_id for channel_id in [channel["id"] for channel in origin_channels_dict_list]
                                                                if self.list[origin][channel_id].number == chan_searchfor]

                        # Append matches to list
                        searchkey_matches.extend(origin_channel_searchkey_matches)

            if not len(searchkey_matches):
                return None

            # Grab first matched channel_id and reverse search the origin
            channel_id = searchkey_matches[0]
            origins = [origin for origin in list(self.list.keys()) if channel_id in list(self.list[origin].keys())]

            # Hopefully we found an origin
            if not len(origins):
                return None
            origin = origins[0]

            # Channel matched, really shouldn't find more than one
            chan_obj = self.list[origin][channel_id]

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

            if keyfind == "number":
                return [self.list[origin][x].number for x in [x["id"] for x in self.get_channels(origin)]]

            else:
                return [self.list[origin][x].dict[keyfind] for x in [x["id"] for x in self.get_channels(origin)]]

        else:

            matches = []
            for origin in list(self.list.keys()):

                if keyfind == "number":
                    next_match = [self.list[origin][x].number for x in [x["id"] for x in self.get_channels(origin)]]

                else:
                    next_match = [self.list[origin][x].dict[keyfind] for x in [x["id"] for x in self.get_channels(origin)]]

                if len(next_match):
                    matches.append(next_match)

            return matches[0]

    def get_channel_dict(self, keyfind, valfind, origin=None):
        """
        Retrieve channel object dict by keyfind property.
        """

        chan_obj = self.find_channel_obj(valfind, searchkey=keyfind, origin=origin)
        if chan_obj:
            return chan_obj.dict
        return None

    def set_channel_status(self, keyfind, valfind, updatedict, origin):
        """
        Set channel object property.
        """
        chan_obj = self.find_channel_obj(valfind, searchkey=keyfind, origin=origin)
        if chan_obj:
            chan_obj.set_status(updatedict)

    def set_channel_enablement_all(self, enablement, origin):
        """
        Enable all channels.
        """

        for fhdhr_id in [x["id"] for x in self.get_channels(origin)]:
            self.list[fhdhr_id].set_enablement(enablement, origin)

    def set_channel_enablement(self, keyfind, valfind, enablement, origin):
        """
        Enable Channel.
        """
        chan_obj = self.find_channel_obj(valfind, searchkey=keyfind, origin=origin)
        if chan_obj:
            chan_obj.set_enablement(enablement)

    def set_channel_favorite(self, keyfind, valfind, enablement, origin):
        """
        Favorite a Channel.
        """
        chan_obj = self.find_channel_obj(valfind, searchkey=keyfind, origin=origin)
        if chan_obj:
            chan_obj.set_favorite(enablement)

    def get_db_channels(self, origin=None):
        """
        Retrieve existing channels from database.
        """

        if not origin:
            origins_list = list(self.list.keys())
        else:
            origins_list = origin.lower()

        if isinstance(origins_list, str):
            origins_list = [origins_list]

        for origin in origins_list:

            self.fhdhr.logger.info("Checking for %s Channel information stored in the database." % origin)
            channel_ids = self.fhdhr.db.get_fhdhr_value("channels", "list", origin) or []

            if len(channel_ids):
                self.fhdhr.logger.info("Found %s existing channels in the database." % str(len(channel_ids)))

            for channel_id in channel_ids:
                channel_obj = Channel(self.fhdhr, self.id_system, origin=origin, channel_id=channel_id)
                channel_id = channel_obj.dict["id"]
                self.list[origin][channel_id] = channel_obj

    def save_db_channels(self, origin=None):
        """
        Save Channel listing to the database.
        """

        if not origin:
            origins_list = list(self.list.keys())

        else:
            origins_list = origin.lower()

        if isinstance(origins_list, str):
            origins_list = [origins_list]

        for origin in origins_list:

            self.fhdhr.logger.debug("Saving %s channels to database." % origin)
            channel_ids = [self.list[origin][x].dict["id"] for x in list(self.list[origin].keys())]
            self.fhdhr.db.set_fhdhr_value("channels", "list", channel_ids, origin)

    def delete_channel(self, fhdhr_id, origin):
        """
        Delete a channel.
        """

        if origin in list(self.list.keys()):

            if fhdhr_id in list(self.list[origin].keys()):

                self.fhdhr.logger.debug("Deleting %s channel. Info: %s" % (origin, fhdhr_id))
                del self.list[origin][fhdhr_id]
                self.save_db_channels(origin)

    def get_channels(self, origin=None, forceupdate=False):
        """
        Pull Channels from origin.
        """

        if not origin:
            origins_list = list(self.list.keys())
        else:
            origins_list = origin.lower().lower()

        if isinstance(origins_list, str):
            origins_list = [origins_list]

        return_chan_list = []
        for origin in origins_list:

            if not len(list(self.list[origin].keys())):
                self.get_db_channels(origin=origin)

            if not forceupdate:
                return_chan_list.extend([self.list[origin][x].dict for x in list(self.list[origin].keys())])

            else:

                channel_origin_id_list = [str(self.list[origin][x].dict["origin_id"]) for x in list(self.list[origin].keys())]

                if self.fhdhr.config.dict["logging"]["level"].upper() == "NOOB":
                    self.fhdhr.logger.noob("Performing Channel Scan for %s. This Process can take some time, Please Wait." % origin)

                else:
                    self.fhdhr.logger.info("Performing Channel Scan for %s." % origin)

                channel_dict_list = self.origins.origins_dict[origin].get_channels()
                self.fhdhr.logger.info("Found %s channels for %s." % (len(channel_dict_list), origin))

                self.fhdhr.logger.info("Performing %s Channel Import, This can take some time, Please wait." % origin)

                newchan = 0
                chan_scan_start = time.time()
                for channel_info in channel_dict_list:

                    chan_existing = str(channel_info["id"]) in channel_origin_id_list

                    if chan_existing:
                        channel_obj = self.find_channel_obj(channel_info["id"], searchkey="origin_id", origin=origin)
                        self.fhdhr.logger.debug("Found Existing %s channel. Info: %s" % (origin, channel_info))

                    else:
                        self.fhdhr.logger.debug("Creating new %s channel. Info: %s" % (origin, channel_info))
                        channel_obj = Channel(self.fhdhr, self.id_system, origin, origin_id=channel_info["id"])

                    channel_id = channel_obj.dict["id"]
                    channel_obj.basics(channel_info)

                    if not chan_existing:
                        self.list[origin][channel_id] = channel_obj
                        newchan += 1

                self.fhdhr.logger.info("%s Channel Import took %s" % (origin, humanized_time(time.time() - chan_scan_start)))

                if not newchan:
                    newchan = "no"
                self.fhdhr.logger.info("Found %s NEW channels for %s." % (newchan, origin))

                self.fhdhr.logger.info("Total %s Channel Count: %s" % (origin, len(self.list[origin].keys())))
                self.save_db_channels(origin=origin)

                self.fhdhr.db.set_fhdhr_value("channels", "scanned_time", time.time(), origin)
                return_chan_list.extend([self.list[origin][x].dict for x in list(self.list[origin].keys())])

        return return_chan_list
