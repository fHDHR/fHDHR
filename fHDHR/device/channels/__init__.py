import datetime

from fHDHR.tools import hours_between_datetime

from .channel import Channel
from .chan_ident import Channel_IDs


class Channels():

    def __init__(self, fhdhr, origin):
        self.fhdhr = fhdhr

        self.origin = origin

        self.id_system = Channel_IDs(fhdhr)

        self.list = {}
        self.list_update_time = None
        self.get_db_channels()
        self.get_channels()

    def get_channel_obj(self, keyfind, valfind):
        return next(self.list[fhdhr_id] for fhdhr_id in list(self.list.keys()) if self.list[fhdhr_id].dict[keyfind] == valfind)

    def get_channel_list(self, keyfind):
        return [self.list[x].dict[keyfind] for x in list(self.list.keys())]

    def set_channel_status(self, keyfind, valfind, enablement):
        self.get_channel_obj(keyfind, valfind).set_status(enablement)

    def get_db_channels(self):
        channel_ids = self.fhdhr.db.get_fhdhr_value("channels", "IDs") or []
        for channel_id in channel_ids:
            channel_obj = Channel(self.fhdhr, self.id_system, channel_id=channel_id)
            channel_id = channel_obj.dict["fhdhr_id"]
            self.list[channel_id] = channel_obj

    def get_channels(self, forceupdate=False):
        """Pull Channels from origin.

        Output a list.

        Don't pull more often than 12 hours.
        """

        updatelist = False
        if not self.list_update_time:
            updatelist = True
        elif hours_between_datetime(self.list_update_time, datetime.datetime.now()) > 12:
            updatelist = True
        elif forceupdate:
            updatelist = True

        if updatelist:
            channel_dict_list = self.origin.get_channels()
            for channel_info in channel_dict_list:
                channel_obj = Channel(self.fhdhr, self.id_system, origin_id=channel_info["id"])
                channel_id = channel_obj.dict["fhdhr_id"]
                channel_obj.basics(channel_info)
                self.list[channel_id] = channel_obj

            if not self.list_update_time:
                self.fhdhr.logger.info("Found " + str(len(self.list)) + " channels for " + str(self.fhdhr.config.dict["main"]["servicename"]))
            self.list_update_time = datetime.datetime.now()

        channel_list = []
        for chan_obj in list(self.list.keys()):
            channel_list.append(self.list[chan_obj].dict)
        return channel_list

    def get_channel_stream(self, channel_number):
        return self.origin.get_channel_stream(self.get_channel_dict("number", channel_number))

    def get_channel_dict(self, keyfind, valfind):
        return self.get_channel_obj(keyfind, valfind).dict
