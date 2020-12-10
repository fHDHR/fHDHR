import os
import time
import datetime
from collections import OrderedDict

from .blocks import blocksEPG


class EPG():

    def __init__(self, fhdhr, channels, originwrapper, alternative_epg):
        self.fhdhr = fhdhr

        self.origin = originwrapper
        self.channels = channels
        self.alternative_epg = alternative_epg

        self.epgdict = {}

        self.epg_methods = self.fhdhr.config.dict["epg"]["method"]
        self.valid_epg_methods = [x for x in self.fhdhr.config.dict["epg"]["valid_epg_methods"] if x and x not in [None, "None"]]

        self.blocks = blocksEPG(self.fhdhr, self.channels)
        self.epg_handling = {
                            "origin": self.origin,
                            "blocks": self.blocks,
                            }
        self.epg_method_selfadd()

        self.def_method = self.fhdhr.config.dict["epg"]["def_method"]
        self.sleeptime = {}
        for epg_method in self.epg_methods:
            if epg_method in list(self.fhdhr.config.dict.keys()):
                if "update_frequency" in list(self.fhdhr.config.dict[epg_method].keys()):
                    self.sleeptime[epg_method] = self.fhdhr.config.dict[epg_method]["update_frequency"]
            if epg_method not in list(self.sleeptime.keys()):
                self.sleeptime[epg_method] = self.fhdhr.config.dict["epg"]["update_frequency"]

        self.epg_update_url = "%s/api/epg?method=update" % (self.fhdhr.api.base)

    def clear_epg_cache(self, method=None):

        if not method:
            method = self.def_method
        if (method == self.fhdhr.config.dict["main"]["dictpopname"] or
           method not in self.fhdhr.config.dict["epg"]["valid_epg_methods"]):
            method = "origin"

        epgtypename = method
        if method in [self.fhdhr.config.dict["main"]["dictpopname"], "origin"]:
            epgtypename = self.fhdhr.config.dict["main"]["dictpopname"]

        self.fhdhr.logger.info("Clearing " + epgtypename + " EPG cache.")

        if hasattr(self.epg_handling[method], 'clear_cache'):
            self.epg_handling[method].clear_cache()

        if method in list(self.epgdict.keys()):
            del self.epgdict[method]

        self.fhdhr.db.delete_fhdhr_value("epg_dict", method)

    def whats_on_now(self, channel_number, method=None):
        nowtime = datetime.datetime.utcnow()
        epgdict = self.get_epg(method)
        try:
            listings = epgdict[channel_number]["listing"]
        except KeyError:
            listings = []
        for listing in listings:
            start_time = datetime.datetime.strptime(listing["time_start"], '%Y%m%d%H%M%S +0000')
            end_time = datetime.datetime.strptime(listing["time_end"], '%Y%m%d%H%M%S +0000')
            if start_time <= nowtime <= end_time:
                epgitem = epgdict[channel_number].copy()
                epgitem["listing"] = [listing]
                return epgitem
        return None

    def whats_on_allchans(self, method=None):

        if not method:
            method = self.def_method
        if (method == self.fhdhr.config.dict["main"]["dictpopname"] or
           method not in self.fhdhr.config.dict["epg"]["valid_epg_methods"]):
            method = "origin"

        channel_guide_list = []
        epgdict = self.get_epg(method)
        if method in ["blocks", "origin", self.fhdhr.config.dict["main"]["dictpopname"]]:
            epgdict = epgdict.copy()
            for c in list(epgdict.keys()):
                chan_obj = self.channels.get_channel_obj("origin_id", epgdict[c]["id"])
                epgdict[chan_obj.number] = epgdict.pop(c)
                epgdict[chan_obj.number]["name"] = chan_obj.dict["name"]
                epgdict[chan_obj.number]["callsign"] = chan_obj.dict["callsign"]
                epgdict[chan_obj.number]["number"] = chan_obj.number
                epgdict[chan_obj.number]["id"] = chan_obj.dict["origin_id"]
                epgdict[chan_obj.number]["thumbnail"] = chan_obj.thumbnail
        for channel_number in list(epgdict.keys()):
            whatson = self.whats_on_now(channel_number, method)
            if whatson:
                channel_guide_list.append(whatson)
        return channel_guide_list

    def get_epg(self, method=None):

        if not method:
            method = self.def_method
        if (method == self.fhdhr.config.dict["main"]["dictpopname"] or
           method not in self.fhdhr.config.dict["epg"]["valid_epg_methods"]):
            method = "origin"

        if method not in list(self.epgdict.keys()):

            epgdict = self.fhdhr.db.get_fhdhr_value("epg_dict", method) or None
            if not epgdict:
                self.update(method)
                self.epgdict[method] = self.fhdhr.db.get_fhdhr_value("epg_dict", method) or {}
            else:
                self.epgdict[method] = epgdict
            return self.epgdict[method]
        else:
            return self.epgdict[method]

    def get_thumbnail(self, itemtype, itemid):
        if itemtype == "channel":
            chandict = self.find_channel_dict(itemid)
            return chandict["thumbnail"]
        elif itemtype == "content":
            progdict = self.find_program_dict(itemid)
            return progdict["thumbnail"]
        return None

    def find_channel_dict(self, channel_id):
        epgdict = self.get_epg()
        channel_list = [epgdict[x] for x in list(epgdict.keys())]
        return next(item for item in channel_list if item["id"] == channel_id) or None

    def find_program_dict(self, event_id):
        epgdict = self.get_epg()
        event_list = []
        for channel in list(epgdict.keys()):
            event_list.extend(epgdict[channel]["listing"])
        return next(item for item in event_list if item["id"] == event_id) or None

    def epg_method_selfadd(self):
        self.fhdhr.logger.info("Checking for Alternative EPG methods.")
        new_epgtype_list = []
        for entry in os.scandir(self.fhdhr.config.internal["paths"]["alternative_epg"]):
            if entry.is_file():
                if entry.name[0] != '_' and entry.name.endswith(".py"):
                    new_epgtype_list.append(str(entry.name[:-3]))
            elif entry.is_dir():
                if entry.name[0] != '_':
                    new_epgtype_list.append(str(entry.name))
        for method in new_epgtype_list:
            self.fhdhr.logger.info("Found %s EPG method." % method)
            self.epg_handling[method] = eval("self.alternative_epg.%s.%sEPG(self.fhdhr, self.channels)" % (method, method))

    def update(self, method=None):

        if (not method or
           method not in self.fhdhr.config.dict["epg"]["valid_epg_methods"]):
            method = self.def_method

        if method == self.fhdhr.config.dict["main"]["dictpopname"]:
            method = "origin"

        epgtypename = method
        if method in [self.fhdhr.config.dict["main"]["dictpopname"], "origin"]:
            epgtypename = self.fhdhr.config.dict["main"]["dictpopname"]

        self.fhdhr.logger.info("Updating " + epgtypename + " EPG cache.")
        if method == 'origin':
            programguide = self.epg_handling['origin'].update_epg(self.channels)
        else:
            programguide = self.epg_handling[method].update_epg()

        programguide = OrderedDict(sorted(programguide.items()))

        for cnum in programguide:
            programguide[cnum]["listing"] = sorted(programguide[cnum]["listing"], key=lambda i: i['time_start'])

        self.epgdict = programguide
        self.fhdhr.db.set_fhdhr_value("epg_dict", method, programguide)
        self.fhdhr.db.set_fhdhr_value("update_time", method, time.time())
        self.fhdhr.logger.info("Wrote " + epgtypename + " EPG cache.")

    def run(self):
        for epg_method in self.epg_methods:
            self.fhdhr.web.session.get(self.epg_update_url)
        try:
            while True:
                for epg_method in self.epg_methods:
                    if time.time() >= (self.fhdhr.db.get_fhdhr_value("update_time", epg_method) + self.sleeptime[epg_method]):
                        self.fhdhr.web.session.get(self.epg_update_url)
                time.sleep(360)
        except KeyboardInterrupt:
            pass
