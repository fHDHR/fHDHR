import time

from fHDHR.tools import humanized_time

from .channel import Channel


class Channels():
    """
    fHDHR Channels system
    """

    def __init__(self, fhdhr, origin, id_system):
        self.fhdhr = fhdhr
        self.origin = origin
        self.id_system = id_system

        # Setup Origin Channels
        self.channel_list = {}
        self.setup()

    """Functions/properties called During init"""

    def setup(self):
        self.fhdhr.logger.info("Initializing %s Channels." % self.origin.name)

        self.get_db_channels()

        chanscan_interval = self.origin.chanscan_interval
        if chanscan_interval:
            self.fhdhr.scheduler.every(chanscan_interval).seconds.do(
                self.fhdhr.scheduler.job_wrapper(self.update_channels)).tag("%s Channel Scan" % self.origin.name)

    """Quick Channels shortcuts"""

    @property
    def count_channels(self):
        return len(self.list_channel_ids)

    @property
    def count_channels_enabled(self):
        return len([channel_id for channel_id in self.list_channel_ids if self.channel_list[channel_id].enabled])

    @property
    def list_channel_dicts(self):
        return [self.channel_list[channel_id].dict for channel_id in self.list_channel_ids]

    @property
    def list_channel_ids(self):
        return [str(x) for x in list(self.channel_list.keys())]

    def create_channel_list(self, searchkey):
        """
        Get a list of channels by keyfind property.
        """

        if searchkey == "number":
            return [self.channel_list[channel_id].number for channel_id in self.list_channel_ids]

        else:
            return [self.channel_list[channel_id].dict[searchkey] for channel_id in self.list_channel_ids
                    if searchkey in list(self.channel_list[channel_id].dict.keys())]

    def get_channels(self, forceupdate=False):
        if forceupdate:
            self.update_channels()
        return self.list_channel_dicts

    def update_channels(self):

        self.fhdhr.logger.noob("Performing Channel Scan for %s. This Process can take some time, Please Wait." % self.origin.name)

        channel_dict_list = self.origin.get_channels()
        self.fhdhr.logger.info("Found %s channels for %s." % (len(channel_dict_list), self.origin.name))

        self.fhdhr.logger.info("Performing %s Channel Import, This can take some time, Please wait." % self.origin.name)

        newchan = 0
        chan_scan_start = time.time()
        for channel_info in channel_dict_list:

            chan_existing = False
            if str(channel_info["id"]) in self.create_channel_list("origin_id"):
                chan_existing = True

            if chan_existing:
                channel_obj = self.find_channel_obj(channel_info["id"], searchkey="origin_id")
            else:
                channel_obj = Channel(self.fhdhr, self.id_system, self.origin, origin_id=channel_info["id"])

            channel_obj.basics(channel_info)
            fhdhr_chan_info = channel_obj.dict

            if chan_existing:
                self.fhdhr.logger.debug("Found Existing %s channel. Info: %s" % (self.origin.name, fhdhr_chan_info))
            else:
                self.fhdhr.logger.debug("Creating new %s channel. Info: %s" % (self.origin.name, fhdhr_chan_info))

            channel_id = channel_obj.dict["id"]

            if not chan_existing:
                self.channel_list[channel_id] = channel_obj
                newchan += 1

        self.fhdhr.logger.info("%s Channel Import took %s" % (self.origin.name, humanized_time(time.time() - chan_scan_start)))

        if not newchan:
            newchan = "no"
        self.fhdhr.logger.info("Found %s NEW channels for %s." % (newchan, self.origin.name))

        self.fhdhr.logger.info("Total %s Channel Count: %s" % (self.origin.name, self.count_channels))
        self.save_db_channels_list()

        self.fhdhr.db.set_fhdhr_value("channels", "scanned_time", time.time(), self.origin.name)

    """Database Functions"""

    def get_db_channels(self):
        """
        Retrieve existing channels from database.
        """

        self.fhdhr.logger.info("Checking for %s Channel information stored in the database." % self.origin.name)
        channel_ids = self.fhdhr.db.get_fhdhr_value("channels", "list", self.origin.name) or []

        if not len(channel_ids):
            self.fhdhr.logger.info("Found NO existing channels in the database.")
            return

        self.fhdhr.logger.info("Found %s existing channels in the database." % str(len(channel_ids)))

        for channel_id in channel_ids:
            channel_obj = Channel(self.fhdhr, self.id_system, self.origin, channel_id=channel_id)
            channel_id = channel_obj.dict["id"]
            self.channel_list[channel_id] = channel_obj

    def save_db_channels_list(self):
        """
        Save Channel listing to the database.
        """

        self.fhdhr.logger.debug("Saving %s channels list to database." % self.origin.name)
        channel_ids = self.list_channel_ids
        self.fhdhr.db.set_fhdhr_value("channels", "list", channel_ids, self.origin.name)

    def delete_channel(self, channel_id):
        """
        Delete a channel.
        """
        if channel_id in self.list_channel_ids:
            self.fhdhr.logger.debug("Deleting %s channel. Info: %s" % (self.origin.name, channel_id))
            channel_object = self.get_channel_object(channel_id)
            channel_object.delete_channel()
            del self.channel_list[channel_id]
            self.save_db_channels_list()

    def save_channel(self, channel_id):
        if channel_id in self.list_channel_ids:
            channel_object = self.get_channel_object(channel_id)
            channel_object.save_channel()

    def delete_all_channels(self):
        """
        Delete all channels.
        """
        for channel_id in self.list_channel_ids:
            self.fhdhr.logger.debug("Deleting %s channel. Info: %s" % (self.origin.name, channel_id))
            channel_object = self.get_channel_object(channel_id)
            channel_object.delete_channel()
            del self.channel_list[channel_id]
            self.save_db_channels_list()

    def save_all_channels(self):
        """
        Save all channels.
        """
        for channel_id in self.list_channel_ids:
            channel_object = self.get_channel_object(channel_id)
            channel_object.save_channel()

    """Set Status of Channel"""

    def set_channel_status(self, chan_searchfor, updatedict, searchkey=None):
        """
        Set channel object property.
        """
        chan_obj = self.find_channel_obj(chan_searchfor, searchkey)
        if chan_obj:
            chan_obj.set_status(updatedict)

    def set_channel_enablement_all(self, enablement):
        """
        Enable all channels.
        """

        for channel_id in self.list_channel_ids:
            chan_obj = self.get_channel_object(channel_id)
            chan_obj.set_enablement(enablement)

    def set_channel_enablement(self, chan_searchfor, enablement, searchkey=None):
        """
        Enable Channel.
        """
        chan_obj = self.find_channel_obj(chan_searchfor, searchkey)
        if chan_obj:
            chan_obj.set_enablement(enablement)

    def set_channel_favorite(self, chan_searchfor, enablement, searchkey=None):
        """
        Favorite a Channel.
        """
        chan_obj = self.find_channel_obj(chan_searchfor, searchkey)
        if chan_obj:
            chan_obj.set_favorite(enablement)

    def get_channel_object(self, channel_id):
        """
        Get a channel Object dict from channel_id.
        """
        if channel_id in self.list_channel_ids:
            return self.channel_list[channel_id]
        return None

    def get_channel_dict(self, channel_id):
        """
        Get a channel Object from channel_id.
        """
        channel_object = self.get_channel_object(channel_id)
        if channel_object:
            return channel_object.dict
        return None

    def find_channel_dict(self, chan_searchfor, searchkey=None):
        """
        Retrieve channel object dict by keyfind property.
        """
        chan_obj = self.find_channel_obj(chan_searchfor, searchkey)
        if chan_obj:
            return chan_obj.dict
        return None

    def find_channel_obj(self, chan_searchfor, searchkey=None):
        """
        Find a channel_obj by keyfind property.
        """
        chan_obj = None

        # Must have a channel to search for
        if not chan_searchfor:
            return None

        # chan_searchfor is an easy to find channel ID
        if chan_searchfor in self.list_channel_ids:
            return self.get_channel_object(chan_searchfor)

        # If a searchkey is provided, this can be helpful for identifying a channel easier
        if isinstance(searchkey, str):
            searchkey_list = [searchkey]
        else:
            searchkey_list = ["id", "number", "name", "callsign"
                              "origin_id", "origin_number", "origin_name", "origin_callsign"]

        # attempt searching by ID and then number
        searchkey_matches = []
        for searchkey in searchkey_list:

            # search for origin channel by searchkey
            if searchkey != "number":
                channel_searchkey_matches = [channel_id for channel_id in [channel["id"] for channel in self.list_channel_dicts]
                                             if searchkey in list(self.channel_list[channel_id].dict.keys())
                                             and self.channel_list[channel_id].dict[searchkey] == chan_searchfor]
            # Searching by number is unique as the @property combines number and subnumber
            else:
                channel_searchkey_matches = [channel_id for channel_id in [channel["id"] for channel in self.list_channel_dicts]
                                             if self.channel_list[channel_id].number == chan_searchfor]

            # Append matches to list
            searchkey_matches.extend(channel_searchkey_matches)

        # searchkey produced no results
        if not len(searchkey_matches):
            return None

        # Channel matched, really shouldn't find more than one
        channel_id = searchkey_matches[0]
        chan_obj = self.get_channel_object(channel_id)

        return chan_obj
