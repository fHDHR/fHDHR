import os
import json
import time
import datetime
from collections import OrderedDict
from multiprocessing import Process

from fHDHR.origin import origin_epg
from .epgtypes import blocks, zap2it


class EPG():

    def __init__(self, settings, channels):
        self.config = settings
        self.channels = channels

        self.origin = origin_epg.originEPG(settings, channels)

        self.epg_method_selfadd()

        self.epg_method = self.config.dict["fhdhr"]["epg_method"]
        if self.epg_method:
            self.sleeptime = self.config.dict[self.epg_method]["epg_update_frequency"]

            self.epg_cache_file = self.config.dict["filedir"]["epg_cache"][self.epg_method]["epg_json"]

            self.epgtypename = self.epg_method
            if self.epg_method in [self.config.dict["main"]["dictpopname"], "origin"]:
                self.epgtypename = self.config.dict["main"]["dictpopname"]

            self.epgscan = Process(target=self.epgServerProcess)
            self.epgscan.start()

    def whats_on_now(self, channel):
        epgdict = self.get_epg()
        listings = epgdict[channel]["listing"]
        for listing in listings:
            nowtime = datetime.datetime.utcnow()
            start_time = datetime.datetime.strptime(listing["time_start"], '%Y%m%d%H%M%S +0000')
            end_time = datetime.datetime.strptime(listing["time_end"], '%Y%m%d%H%M%S +0000')
            if start_time <= nowtime <= end_time:
                epgitem = epgdict[channel].copy()
                epgitem["listing"] = [listing]
                return epgitem
        return None

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

    def epg_method_selfadd(self):
        for method in self.config.dict["main"]["valid_epg_methods"]:
            if method not in [None, "None", "origin", self.config.dict["main"]["dictpopname"]]:
                exec("%s = %s" % ("self." + str(method), str(method) + "." + str(method) + "EPG(self.config, self.channels)"))

    def update(self):

        print("Updating " + self.epgtypename + " EPG cache file.")
        method_to_call = getattr(self, self.epg_method)
        func_to_call = getattr(method_to_call, 'update_epg')
        programguide = func_to_call()

        for chan in list(programguide.keys()):
            floatnum = str(float(chan))
            programguide[floatnum] = programguide.pop(chan)
            programguide[floatnum]["number"] = floatnum

        programguide = OrderedDict(sorted(programguide.items()))

        for cnum in programguide:
            programguide[cnum]["listing"] = sorted(programguide[cnum]["listing"], key=lambda i: i['time_start'])

        with open(self.epg_cache_file, 'w') as epgfile:
            epgfile.write(json.dumps(programguide, indent=4))
        print("Wrote " + self.epgtypename + " EPG cache file.")

    def epgServerProcess(self):
        print("Starting EPG thread...")

        try:
            while True:
                self.update()
                time.sleep(self.sleeptime)
        except KeyboardInterrupt:
            pass
