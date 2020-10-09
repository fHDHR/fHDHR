import os
import json
from collections import OrderedDict

from . import blocks, zap2it


class EPGTypes():

    def __init__(self, settings, origserv):
        self.config = settings
        self.origin = origserv

        self.blocks = blocks.BlocksEPG(settings, origserv)
        self.zap2it = zap2it.ZapEPG(settings, origserv)

        self.epg_method = self.config.dict["fhdhr"]["epg_method"]
        if self.epg_method:
            self.epg_cache_file = self.config.dict["filedir"]["epg_cache"][self.epg_method]["epg_json"]

            self.epgtypename = self.epg_method
            if self.epg_method == self.config.dict["main"]["dictpopname"] or self.epg_method == "origin":
                self.epgtypename = self.config.dict["main"]["dictpopname"]

    def get_epg(self):
        epgdict = None
        if os.path.isfile(self.epg_cache_file):
            with open(self.epg_cache_file, 'r') as epgfile:
                epgdict = json.load(epgfile)
        return epgdict

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
        channel_list = []
        for channel in list(epgdict.keys()):
            channel_list.append(epgdict[channel])
        return next(item for item in channel_list if item["id"] == channel_id)

    def find_program_dict(self, event_id):
        epgdict = self.get_epg()
        event_list = []
        for channel in list(epgdict.keys()):
            event_list.extend(epgdict[channel]["listing"])
        return next(item for item in event_list if item["id"] == event_id)

    def update(self):

        print("Updating " + self.epgtypename + " EPG cache file.")
        method_to_call = getattr(self, self.epg_method)
        func_to_call = getattr(method_to_call, 'update_epg')
        programguide = func_to_call()

        programguide = OrderedDict(sorted(programguide.items()))
        for cnum in programguide:
            programguide[cnum]["listing"] = sorted(programguide[cnum]["listing"], key=lambda i: i['time_start'])

        with open(self.epg_cache_file, 'w') as epgfile:
            epgfile.write(json.dumps(programguide, indent=4))
        print("Wrote " + self.epgtypename + " EPG cache file.")
