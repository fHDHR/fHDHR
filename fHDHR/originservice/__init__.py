import datetime
from collections import OrderedDict

from . import plutotv as serviceorigin
from fHDHR.tools import hours_between_datetime
from fHDHR.fHDHRerrors import LoginError


class OriginService():

    def __init__(self, settings):
        self.config = settings
        self.serviceorigin = serviceorigin.fHDHRservice(settings)
        if not self.serviceorigin.login():
            raise LoginError(self.config.dict["main"]["servicename"] + " Login Failed.")

        self.channels = {
                        "list": {},
                        "list_updated": None,
                        }

    def append_channel_info(self, chanlist):
        for chan in chanlist:
            if chan["number"] not in list(self.channels["list"].keys()):
                self.channels["list"][chan["number"]] = {}
            for chankey in list(chan.keys()):
                self.channels["list"][chan["number"]][chankey] = chan[chankey]
        self.channel_order()

    def channel_order(self):
        self.channels["list"] = OrderedDict(sorted(self.channels["list"].items()))

    def get_channels(self, forceupdate=False):

        updatelist = False
        if not self.channels["list_updated"]:
            updatelist = True
        elif hours_between_datetime(self.channels["list_updated"], datetime.datetime.now()) > 12:
            updatelist = True
        elif forceupdate:
            updatelist = True

        if updatelist:
            chanlist = self.serviceorigin.get_channels()
            self.append_channel_info(chanlist)
            self.channels["list_updated"] = datetime.datetime.now()

        channel_list = []
        for chandict in list(self.channels["list"].keys()):
            channel_list.append(self.channels["list"][chandict])
        return channel_list

    def get_fhdhr_stream_url(self, base_url, channel):
        return ('%s%s/auto/v%s' %
                ("http://",
                 base_url,
                 channel['number']))

    def get_station_list(self, base_url):
        station_list = []

        for c in self.get_channels():
            station_list.append({
                                 'GuideNumber': c['number'],
                                 'GuideName': c['name'],
                                 'URL': self.get_fhdhr_stream_url(base_url, c),
                                })
        return station_list

    def get_channel_stream(self, channel_number):
        if channel_number not in list(self.channels["list"].keys()):
            self.get_channels()
        if channel_number not in list(self.channels["list"].keys()):
            return None
        if "stream_url" not in list(self.channels["list"][channel_number].keys()):
            chandict = self.get_channel_dict("number", channel_number)
            streamlist, caching = self.serviceorigin.get_channel_stream(chandict, self.channels["list"])
            if caching:
                self.append_channel_info(streamlist)
                return self.channels["list"][channel_number]["stream_url"]
            else:
                chanstreamdict = next(item for item in streamlist if item["number"] == channel_number)
                return chanstreamdict["stream_url"]
        return self.channels["list"][channel_number]["stream_url"]

    def get_station_total(self):
        chanlist = self.get_channels()
        return len(chanlist)

    def get_channel_dict(self, keyfind, valfind):
        chanlist = self.get_channels()
        return next(item for item in chanlist if item[keyfind] == valfind)

    def update_epg(self):
        return self.serviceorigin.update_epg()
