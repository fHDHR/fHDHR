import time

from fHDHR.tools import humanized_time

from .channel import Channel
from .chan_ident import Channel_IDs


class Channels():

    def __init__(self, fhdhr, originwrapper):
        self.fhdhr = fhdhr

        self.origin = originwrapper

        self.id_system = Channel_IDs(fhdhr)

        self.list = {}

        self.get_db_channels()

    def get_channel_obj(self, keyfind, valfind):
        if keyfind == "number":
            return next(self.list[fhdhr_id] for fhdhr_id in [x["id"] for x in self.get_channels()] if self.list[fhdhr_id].number == valfind) or None
        else:
            return next(self.list[fhdhr_id] for fhdhr_id in [x["id"] for x in self.get_channels()] if self.list[fhdhr_id].dict[keyfind] == valfind) or None

    def get_channel_list(self, keyfind):
        if keyfind == "number":
            return [self.list[x].number for x in [x["id"] for x in self.get_channels()]]
        else:
            return [self.list[x].dict[keyfind] for x in [x["id"] for x in self.get_channels()]]

    def set_channel_status(self, keyfind, valfind, updatedict):
        self.get_channel_obj(keyfind, valfind).set_status(updatedict)

    def set_channel_enablement_all(self, enablement):
        for fhdhr_id in [x["id"] for x in self.get_channels()]:
            self.list[fhdhr_id].set_enablement(enablement)

    def set_channel_enablement(self, keyfind, valfind, enablement):
        self.get_channel_obj(keyfind, valfind).set_enablement(enablement)

    def set_channel_favorite(self, keyfind, valfind, enablement):
        self.get_channel_obj(keyfind, valfind).set_favorite(enablement)

    def get_db_channels(self):
        self.fhdhr.logger.info("Checking for Channel information stored in the database.")
        channel_ids = self.fhdhr.db.get_fhdhr_value("channels", "list") or []
        if len(channel_ids):
            self.fhdhr.logger.info("Found %s existing channels in the database." % str(len(channel_ids)))
            for channel_id in channel_ids:
                channel_obj = Channel(self.fhdhr, self.id_system, channel_id=channel_id)
                channel_id = channel_obj.dict["id"]
                self.list[channel_id] = channel_obj

    def save_db_channels(self):
        channel_ids = [x["id"] for x in self.get_channels()]
        self.fhdhr.db.set_fhdhr_value("channels", "list", channel_ids)

    def get_channels(self, forceupdate=False):
        """Pull Channels from origin.

        Output a list.

        Don't pull more often than 12 hours.
        """

        if not len(list(self.list.keys())):
            self.get_db_channels()

        if not forceupdate:
            return [self.list[x].dict for x in list(self.list.keys())]

        channel_origin_id_list = [str(self.list[x].dict["origin_id"]) for x in list(self.list.keys())]

        self.fhdhr.logger.info("Performing Channel Scan.")

        channel_dict_list = self.origin.get_channels()
        self.fhdhr.logger.info("Found %s channels for %s." % (len(channel_dict_list), self.fhdhr.config.dict["main"]["servicename"]))

        self.fhdhr.logger.info("Performing Channel Import, This can take some time, Please wait.")

        newchan = 0
        chan_scan_start = time.time()
        for channel_info in channel_dict_list:

            chan_existing = str(channel_info["id"]) in channel_origin_id_list

            if chan_existing:
                channel_obj = self.get_channel_obj("origin_id", channel_info["id"])
            else:
                channel_obj = Channel(self.fhdhr, self.id_system, origin_id=channel_info["id"])

            channel_id = channel_obj.dict["id"]
            channel_obj.basics(channel_info)
            if not chan_existing:
                self.list[channel_id] = channel_obj
                newchan += 1

        self.fhdhr.logger.info("Channel Import took %s" % humanized_time(time.time() - chan_scan_start))

        if not newchan:
            newchan = "no"
        self.fhdhr.logger.info("Found %s NEW channels." % newchan)

        self.fhdhr.logger.info("Total Channel Count: %s" % len(self.list.keys()))
        self.save_db_channels()

        self.fhdhr.db.set_fhdhr_value("channels", "scanned_time", time.time())

        return [self.list[x].dict for x in list(self.list.keys())]

    def get_channel_stream(self, stream_args):
        return self.origin.get_channel_stream(self.get_channel_dict("number", stream_args["channel"]), stream_args)

    def get_channel_dict(self, keyfind, valfind):
        return self.get_channel_obj(keyfind, valfind).dict
