import datetime
from collections import OrderedDict

from fHDHR.tools import hours_between_datetime


class ChannelNumbers():

    def __init__(self, settings, logger, db):
        self.config = settings
        self.logger = logger
        self.db = db

    def get_number(self, channel_id):
        cnumbers = self.db.get_fhdhr_value("channel_numbers", "list") or {}
        if channel_id in list(cnumbers.keys()):
            return cnumbers[channel_id]

        used_numbers = []
        for channel_id in list(cnumbers.keys()):
            used_numbers.append(cnumbers[channel_id])

        for i in range(1, 1000):
            if str(float(i)) not in used_numbers:
                break
        return str(float(i))

    def set_number(self, channel_id, channel_number):
        cnumbers = self.db.get_fhdhr_value("channel_numbers", "list") or {}
        cnumbers[channel_id] = str(float(channel_number))
        self.db.set_fhdhr_value("channel_numbers", "list", cnumbers)


class Channels():

    def __init__(self, settings, origin, logger, db):
        self.config = settings
        self.logger = logger
        self.origin = origin
        self.db = db

        self.channel_numbers = ChannelNumbers(settings, logger, db)

        self.list = {}
        self.list_update_time = None
        self.get_channels()

    def get_origin_status(self):
        try:
            return self.origin.get_status_dict()
        except AttributeError:
            return {}

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
            channel_dict_list = self.verify_channel_info(channel_dict_list)
            self.append_channel_info(channel_dict_list)
            if not self.list_update_time:
                self.logger.info("Found " + str(len(self.list)) + " channels for " + str(self.config.dict["main"]["servicename"]))
            self.list_update_time = datetime.datetime.now()

        channel_list = []
        for chandict in list(self.list.keys()):
            channel_list.append(self.list[chandict])
        return channel_list

    def get_station_list(self, base_url):
        station_list = []

        for c in self.get_channels():
            station_list.append({
                                 'GuideNumber': c['number'],
                                 'GuideName': c['name'],
                                 'URL': self.get_fhdhr_stream_url(base_url, c['number']),
                                })
        return station_list

    def get_channel_stream(self, channel_number):
        if channel_number not in list(self.list.keys()):
            self.get_channels()
        if channel_number not in list(self.list.keys()):
            return None
        if "stream_url" not in list(self.list[channel_number].keys()):
            chandict = self.get_channel_dict("number", channel_number)
            streamlist, caching = self.origin.get_channel_stream(chandict, self.list)
            if caching:
                self.append_channel_info(streamlist)
                return self.list[channel_number]["stream_url"]
            else:
                chanstreamdict = next(item for item in streamlist if item["number"] == channel_number)
                return chanstreamdict["stream_url"]
        return self.list[channel_number]["stream_url"]

    def get_station_total(self):
        return len(list(self.list.keys()))

    def get_channel_dict(self, keyfind, valfind):
        chanlist = self.get_channels()
        return next(item for item in chanlist if item[keyfind] == valfind)

    def get_fhdhr_stream_url(self, base_url, channel_number):
        return ('%s/auto/v%s' %
                (base_url,
                 channel_number))

    def verify_channel_info(self, channel_dict_list):
        """Some Channel Information is Critical"""
        cleaned_channel_dict_list = []
        for station_item in channel_dict_list:
            if "callsign" not in list(station_item.keys()):
                station_item["callsign"] = station_item["name"]
            if "id" not in list(station_item.keys()):
                station_item["id"] = station_item["name"]
            if "number" not in list(station_item.keys()):
                station_item["number"] = self.channel_numbers.get_number(station_item["id"])
            else:
                station_item["number"] = str(float(station_item["number"]))
            self.channel_numbers.set_number(station_item["id"], station_item["number"])
            cleaned_channel_dict_list.append(station_item)
        return cleaned_channel_dict_list

    def append_channel_info(self, channel_dict_list):
        """Update the list dict

        Take the channel dict list given.
        """
        for chan in channel_dict_list:
            if chan["number"] not in list(self.list.keys()):
                self.list[chan["number"]] = {}
            for chankey in list(chan.keys()):
                self.list[chan["number"]][chankey] = chan[chankey]
        self.channel_order()

    def channel_order(self):
        """Verify the Channel Order"""
        self.list = OrderedDict(sorted(self.list.items()))
