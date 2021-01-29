import time

from fHDHR.tools import humanized_time

from .channel import Channel
from .chan_ident import Channel_IDs


class Channels():

    def __init__(self, fhdhr, origins):
        self.fhdhr = fhdhr

        self.origins = origins

        self.id_system = Channel_IDs(fhdhr, origins)

        self.list = {}
        for origin in list(self.origins.origins_dict.keys()):
            self.list[origin] = {}

        self.get_db_channels()

    def get_channel_obj(self, keyfind, valfind, origin=None):
        if origin:
            origin = origin.lower()
            if keyfind == "number":
                matches = [self.list[origin][x].dict["id"] for x in list(self.list[origin].keys()) if self.list[origin][x].number == valfind]
            else:
                matches = [self.list[origin][x].dict["id"] for x in list(self.list[origin].keys()) if self.list[origin][x].dict[keyfind] == valfind]
            if len(matches):
                return self.list[origin][matches[0]]
        else:
            matches = []
            for origin in list(self.list.keys()):
                if keyfind == "number":
                    matches = [self.list[origin][x].dict["id"] for x in list(self.list[origin].keys()) if self.list[origin][x].number == valfind]
                else:
                    matches = [self.list[origin][x].dict["id"] for x in list(self.list[origin].keys()) if self.list[origin][x].dict[keyfind] == valfind]
                if len(matches):
                    return self.list[origin][matches[0]]
            if len(matches):
                return self.list[origin][matches[0]]
        return None

    def get_channel_list(self, keyfind, origin=None):
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
        chan_obj = self.get_channel_obj(keyfind, valfind, origin)
        if chan_obj:
            return chan_obj.dict
        return None

    def set_channel_status(self, keyfind, valfind, updatedict, origin):
        self.get_channel_obj(keyfind, valfind, origin).set_status(updatedict)

    def set_channel_enablement_all(self, enablement, origin):
        for fhdhr_id in [x["id"] for x in self.get_channels(origin)]:
            self.list[fhdhr_id].set_enablement(enablement, origin)

    def set_channel_enablement(self, keyfind, valfind, enablement, origin):
        self.get_channel_obj(keyfind, valfind, origin).set_enablement(enablement)

    def set_channel_favorite(self, keyfind, valfind, enablement, origin):
        self.get_channel_obj(keyfind, valfind, origin).set_favorite(enablement)

    def get_db_channels(self, origin=None):

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
        if not origin:
            origins_list = list(self.list.keys())
        else:
            origins_list = origin.lower()

        if isinstance(origins_list, str):
            origins_list = [origins_list]

        for origin in origins_list:
            channel_ids = [self.list[origin][x].dict["id"] for x in list(self.list[origin].keys())]
            self.fhdhr.db.set_fhdhr_value("channels", "list", channel_ids, origin)

    def get_channels(self, origin=None, forceupdate=False):
        """Pull Channels from origin.

        Output a list.

        Don't pull more often than 12 hours.
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

                self.fhdhr.logger.info("Performing Channel Scan for %s." % origin)

                channel_dict_list = self.origins.origins_dict[origin].get_channels()
                self.fhdhr.logger.info("Found %s channels for %s." % (len(channel_dict_list), origin))

                self.fhdhr.logger.info("Performing Channel Import, This can take some time, Please wait.")

                newchan = 0
                chan_scan_start = time.time()
                for channel_info in channel_dict_list:

                    chan_existing = str(channel_info["id"]) in channel_origin_id_list

                    if chan_existing:
                        channel_obj = self.get_channel_obj("origin_id", channel_info["id"], origin)
                    else:
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

    def get_channel_stream(self, stream_args, origin):
        return self.origins.origins_dict[origin].get_channel_stream(self.get_channel_dict("number", stream_args["channel"]), stream_args)
