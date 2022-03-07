import time

from fHDHR.tools import channel_sort
from .channel import Channel


class Channels():
    """
    fHDHR Channels system
    """

    def __init__(self, fhdhr, origin_obj, id_system):
        self.fhdhr = fhdhr
        self.origin_obj = origin_obj
        self.origin_name = origin_obj.name
        self.id_system = id_system

        # Setup Origin Channels
        self.channel_list = {}
        self.setup()

    """Functions/properties called During init"""

    def setup(self):
        self.fhdhr.logger.info("Initializing %s Channels." % self.origin_name)

        self.get_db_channels()

        self.schedule_scan()

    """Functions relating to scheduler"""

    def get_scheduled_time(self):
        return self.fhdhr.scheduler.get_scheduled_time(self.scan_tag)

    @property
    def scan_tag(self):
        return "%s Channel Scan" % self.origin_name

    def set_schedule_scan_interval(self, interval=None):
        if not interval:
            interval = self.origin_obj.chanscan_interval
        if interval != self.origin_obj.chanscan_interval:
            self.fhdhr.config.write("chanscan_interval", interval, self.origin_name)
        return self.origin_obj.chanscan_interval

    def schedule_scan(self, interval=None):
        interval = self.set_schedule_scan_interval(interval)
        self.fhdhr.scheduler.every(interval).seconds.do(
            self.fhdhr.scheduler.job_wrapper(self.scan_channels)).tag(self.scan_tag)

    @property
    def check_schedule_scan(self):
        if self.scan_tag in self.fhdhr.scheduler.list_tags:
            return True
        return False

    def run_schedule_scan(self):
        """Runs the `scan_channels` function via the scheduler."""
        if self.check_schedule_scan:
            self.fhdhr.scheduler.run_from_tag(self.scan_tag)
            return
        """
        Add to scheduler, run from scheduler, remove from scheduler.
        Doing this as it might have been manually removed from the scheduler.
        """
        self.schedule_scan()
        if self.check_schedule_scan:
            self.fhdhr.scheduler.run_from_tag(self.scan_tag)
            self.remove_schedule_scan()

    def remove_schedule_scan(self):
        self.fhdhr.scheduler.remove(self.scan_tag)
        self.fhdhr.config.write("chanscan_interval", None, self.origin_name)

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
    def dict_of_channel_dicts_by_number(self):
        channels_dict = {}
        for channel_id in self.list_channel_ids:
            channels_dict[self.channel_list[channel_id].number] = self.channel_list[channel_id].dict
        return channels_dict

    @property
    def list_channel_ids(self):
        return [str(x) for x in list(self.channel_list.keys())]

    @property
    def list_channel_numbers(self):
        return [str(x.number) for x in list(self.channel_list.keys())]

    @property
    def sorted_channel_number_list(self):
        return channel_sort(self.list_channel_numbers)

    @property
    def sorted_channel_dicts(self):
        channels_dict = self.dict_of_channel_dicts_by_number
        # Sort the channels
        sorted_channel_list = channel_sort(list(channels_dict.keys()))
        sorted_chan_guide = []
        for channel_number in sorted_channel_list:
            sorted_chan_guide.append(channels_dict[channel_number])
        return sorted_chan_guide

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
            self.scan_channels()
        return self.list_channel_dicts

    def scan_channels(self):

        self.fhdhr.logger.noob("Performing Channel Scan for %s. This Process can take some time, Please Wait." % self.origin_name)

        channel_dict_list = self.origin_obj.get_channels()
        self.fhdhr.logger.info("Found %s channels for %s." % (len(channel_dict_list), self.origin_name))

        self.fhdhr.logger.info("Performing %s Channel Import, This can take some time, Please wait." % self.origin_name)

        newchan = 0
        chan_scan_start = time.time()
        for channel_info in channel_dict_list:

            chan_existing = False
            if str(channel_info["id"]) in self.create_channel_list("origin_id"):
                chan_existing = True

            if chan_existing:
                channel_obj = self.find_channel_obj(channel_info["id"], searchkey="origin_id")
            else:
                channel_obj = Channel(self.fhdhr, self.id_system, self.origin_obj, origin_id=channel_info["id"])

            channel_obj.basics(channel_info)
            fhdhr_chan_info = channel_obj.dict

            if chan_existing:
                self.fhdhr.logger.debug("Found Existing %s channel. Info: %s" % (self.origin_name, fhdhr_chan_info))
            else:
                self.fhdhr.logger.debug("Creating new %s channel. Info: %s" % (self.origin_name, fhdhr_chan_info))

            channel_id = channel_obj.dict["id"]

            if not chan_existing:
                self.channel_list[channel_id] = channel_obj
                newchan += 1

        self.fhdhr.logger.info("%s Channel Import took %s" % (self.origin_name, self.fhdhr.time.humanized_time(time.time() - chan_scan_start)))

        if not newchan:
            newchan = "no"
        self.fhdhr.logger.info("Found %s NEW channels for %s." % (newchan, self.origin_name))

        self.fhdhr.logger.info("Total %s Channel Count: %s" % (self.origin_name, self.count_channels))
        self.save_db_channels_list()

        self.fhdhr.db.set_fhdhr_value("channels", "scanned_time", time.time(), self.origin_name)

    """Database Functions"""

    def get_db_channels(self):
        """
        Retrieve existing channels from database.
        """

        self.fhdhr.logger.info("Checking for %s Channel information stored in the database." % self.origin_name)
        channel_ids = self.fhdhr.db.get_fhdhr_value("channels", "list", self.origin_name) or []

        if not len(channel_ids):
            self.fhdhr.logger.info("Found NO existing channels in the database.")
            return

        self.fhdhr.logger.info("Found %s existing channels in the database." % str(len(channel_ids)))

        for channel_id in channel_ids:
            channel_obj = Channel(self.fhdhr, self.id_system, self.origin_obj, channel_id=channel_id)
            channel_id = channel_obj.dict["id"]
            self.channel_list[channel_id] = channel_obj

    def save_db_channels_list(self):
        """
        Save Channel listing to the database.
        """

        self.fhdhr.logger.debug("Saving %s channels list to database." % self.origin_name)
        channel_ids = self.list_channel_ids
        self.fhdhr.db.set_fhdhr_value("channels", "list", channel_ids, self.origin_name)

    def delete_channel(self, channel_id):
        """
        Delete a channel.
        """
        if channel_id in self.list_channel_ids:
            self.fhdhr.logger.debug("Deleting %s channel. Info: %s" % (self.origin_name, channel_id))
            channel_object = self.get_channel_obj(channel_id)
            channel_object.delete_channel()
            del self.channel_list[channel_id]
            self.save_db_channels_list()

    def save_channel(self, channel_id):
        if channel_id in self.list_channel_ids:
            channel_object = self.get_channel_obj(channel_id)
            channel_object.save_channel()

    def delete_all_channels(self):
        """
        Delete all channels.
        """
        for channel_id in self.list_channel_ids:
            self.fhdhr.logger.debug("Deleting %s channel. Info: %s" % (self.origin_name, channel_id))
            channel_object = self.get_channel_obj(channel_id)
            channel_object.delete_channel()
            del self.channel_list[channel_id]
            self.save_db_channels_list()

    def save_all_channels(self):
        """
        Save all channels.
        """
        for channel_id in self.list_channel_ids:
            channel_object = self.get_channel_obj(channel_id)
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
            chan_obj = self.get_channel_obj(channel_id)
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

    def get_channel_obj(self, channel_id):
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
        channel_object = self.get_channel_obj(channel_id)
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
            return self.get_channel_obj(chan_searchfor)

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
        chan_obj = self.get_channel_obj(channel_id)

        return chan_obj
