import os
import time
import datetime

from fHDHR.tools import channel_sort

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

        self.epg_update_url = "/api/epg?method=update"

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

    def whats_on_now(self, channel_number, method=None, chan_obj=None, chan_dict=None):
        nowtime = time.time()
        epgdict = self.get_epg(method)
        try:
            listings = epgdict[channel_number]["listing"]
        except KeyError:
            listings = []
        for listing in listings:
            for time_item in ["time_start", "time_end"]:
                time_value = listing[time_item]
                if str(time_value).endswith("+00:00"):
                    listing[time_item] = datetime.datetime.strptime(time_value, '%Y%m%d%H%M%S +00:00').timestamp()
                elif str(time_value).endswith("+0000"):
                    listing[time_item] = datetime.datetime.strptime(time_value, '%Y%m%d%H%M%S +0000').timestamp()
                else:
                    listing[time_item] = int(time_value)
            if int(listing["time_start"]) <= nowtime <= int(listing["time_end"]):
                epgitem = epgdict[channel_number].copy()
                epgitem["listing"] = [listing]
                return epgitem
        epgitem = epgdict[channel_number].copy()
        epgitem["listing"] = [self.blocks.empty_listing(chan_obj=None, chan_dict=None)]
        return epgitem

    def whats_on_allchans(self, method=None):

        if not method:
            method = self.def_method
        if (method == self.fhdhr.config.dict["main"]["dictpopname"] or
           method not in self.fhdhr.config.dict["epg"]["valid_epg_methods"]):
            method = "origin"

        channel_guide_dict = {}
        epgdict = self.get_epg(method)
        epgdict = epgdict.copy()
        for c in list(epgdict.keys()):
            if method in ["blocks", "origin", self.fhdhr.config.dict["main"]["dictpopname"]]:
                chan_obj = self.channels.get_channel_obj("origin_id", epgdict[c]["id"])
                channel_number = chan_obj.number
                epgdict[channel_number] = epgdict.pop(c)
                epgdict[channel_number]["name"] = chan_obj.dict["name"]
                epgdict[channel_number]["callsign"] = chan_obj.dict["callsign"]
                epgdict[channel_number]["number"] = chan_obj.number
                epgdict[channel_number]["id"] = chan_obj.dict["origin_id"]
                epgdict[channel_number]["thumbnail"] = chan_obj.thumbnail
            else:
                chan_obj = None
                channel_number = c
            whatson = self.whats_on_now(channel_number, method, chan_dict=epgdict, chan_obj=chan_obj)
            if whatson:
                channel_guide_dict[channel_number] = whatson
        return channel_guide_dict

    def get_epg(self, method=None):

        if not method:
            method = self.def_method
        if (method == self.fhdhr.config.dict["main"]["dictpopname"] or
           method not in self.fhdhr.config.dict["epg"]["valid_epg_methods"]):
            method = "origin"

        if method in list(self.epgdict.keys()):
            return self.epgdict[method]

        self.update(method)
        self.epgdict[method] = self.fhdhr.db.get_fhdhr_value("epg_dict", method) or {}
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

        # sort the channel listings by time stamp
        for cnum in list(programguide.keys()):
            programguide[cnum]["listing"] = sorted(programguide[cnum]["listing"], key=lambda i: i['time_start'])

        # Gernate Block periods for between EPG data, if missing
        clean_prog_guide = {}
        desired_start_time = (datetime.datetime.today() + datetime.timedelta(days=self.fhdhr.config.dict["epg"]["reverse_days"])).timestamp()
        desired_end_time = (datetime.datetime.today() + datetime.timedelta(days=self.fhdhr.config.dict["epg"]["forward_days"])).timestamp()
        for cnum in list(programguide.keys()):

            if cnum not in list(clean_prog_guide.keys()):
                clean_prog_guide[cnum] = programguide[cnum].copy()
                clean_prog_guide[cnum]["listing"] = []

            if method in ["blocks", "origin", self.fhdhr.config.dict["main"]["dictpopname"]]:
                chan_obj = self.channels.get_channel_obj("origin_id", programguide[cnum]["id"])
            else:
                chan_obj = None

            # Generate Blocks for Channels containing No Lisiings
            if not len(programguide[cnum]["listing"]):
                timestamps = self.blocks.timestamps_between(desired_start_time, desired_end_time)
                clean_prog_dicts = self.blocks.empty_channel_epg(timestamps, chan_dict=programguide[cnum], chan_obj=chan_obj)
                clean_prog_guide[cnum]["listing"].extend(clean_prog_dicts)

            else:

                # Clean Timetamps from old xmltv method to timestamps
                progindex = 0
                for program_item in programguide[cnum]["listing"]:
                    for time_item in ["time_start", "time_end"]:
                        time_value = programguide[cnum]["listing"][progindex][time_item]
                        if str(time_value).endswith("+00:00"):
                            programguide[cnum]["listing"][progindex][time_item] = datetime.datetime.strptime(time_value, '%Y%m%d%H%M%S +00:00').timestamp()
                        elif str(time_value).endswith("+0000"):
                            programguide[cnum]["listing"][progindex][time_item] = datetime.datetime.strptime(time_value, '%Y%m%d%H%M%S +0000').timestamp()
                        else:
                            programguide[cnum]["listing"][progindex][time_item] = int(time_value)
                    progindex += 1

                # Generate time before the listing actually starts
                first_prog_time = programguide[cnum]["listing"][0]['time_start']
                if desired_start_time < first_prog_time:
                    timestamps = self.blocks.timestamps_between(desired_start_time, first_prog_time)
                    clean_prog_dicts = self.blocks.empty_channel_epg(timestamps, chan_dict=programguide[cnum], chan_obj=chan_obj)
                    clean_prog_guide[cnum]["listing"].extend(clean_prog_dicts)

                # Generate time blocks between events if chunks of time are missing
                progindex = 0
                for program_item in programguide[cnum]["listing"]:
                    try:
                        nextprog_dict = programguide[cnum]["listing"][progindex + 1]
                    except IndexError:
                        nextprog_dict = None
                    if not nextprog_dict:
                        clean_prog_guide[cnum]["listing"].append(program_item)
                    else:
                        if nextprog_dict['time_start'] > program_item['time_end']:
                            timestamps = self.blocks.timestamps_between(program_item['time_end'], nextprog_dict['time_start'])
                            clean_prog_dicts = self.blocks.empty_channel_epg(timestamps, chan_dict=programguide[cnum], chan_obj=chan_obj)
                            clean_prog_guide[cnum]["listing"].extend(clean_prog_dicts)
                        else:
                            clean_prog_guide[cnum]["listing"].append(program_item)
                        progindex += 1

                # Generate time after the listing actually ends
                end_prog_time = programguide[cnum]["listing"][progindex]['time_end']
                if desired_end_time > end_prog_time:
                    timestamps = self.blocks.timestamps_between(end_prog_time, desired_end_time)
                    clean_prog_dicts = self.blocks.empty_channel_epg(timestamps, chan_dict=programguide[cnum], chan_obj=chan_obj)
                    clean_prog_guide[cnum]["listing"].extend(clean_prog_dicts)

        programguide = clean_prog_guide.copy()

        # if a stock method, generate Blocks EPG for missing channels
        if method in ["blocks", "origin", self.fhdhr.config.dict["main"]["dictpopname"]]:
            timestamps = self.blocks.timestamps
            for fhdhr_id in [x["id"] for x in self.channels.get_channels()]:
                chan_obj = self.channels.list[fhdhr_id]
                if str(chan_obj.number) not in list(programguide.keys()):
                    programguide[str(chan_obj.number)] = chan_obj.epgdict
                    clean_prog_dicts = self.blocks.empty_channel_epg(timestamps, chan_obj=chan_obj)
                    programguide[str(chan_obj.number)]["listing"].extend(clean_prog_dicts)

        # Make Thumbnails for missing thumbnails
        for cnum in list(programguide.keys()):
            if not programguide[cnum]["thumbnail"]:
                programguide[cnum]["thumbnail"] = "/api/images?method=generate&type=channel&message=%s" % programguide[cnum]["number"]
            programguide[cnum]["listing"] = sorted(programguide[cnum]["listing"], key=lambda i: i['time_start'])
            prog_index = 0
            for program_item in programguide[cnum]["listing"]:
                if not programguide[cnum]["listing"][prog_index]["thumbnail"]:
                    programguide[cnum]["listing"][prog_index]["thumbnail"] = programguide[cnum]["thumbnail"]
                prog_index += 1

        # Get Totals
        total_channels = len(list(programguide.keys()))
        total_programs = 0

        # Sort the channels
        sorted_channel_list = channel_sort(list(programguide.keys()))
        sorted_chan_guide = {}
        for channel in sorted_channel_list:
            total_programs += len(programguide[cnum]["listing"])
            sorted_chan_guide[channel] = programguide[channel]

        self.epgdict[method] = sorted_chan_guide
        self.fhdhr.db.set_fhdhr_value("epg_dict", method, programguide)
        self.fhdhr.db.set_fhdhr_value("update_time", method, time.time())
        self.fhdhr.logger.info("Wrote %s EPG cache. %s Programs for %s Channels" % (epgtypename, total_programs, total_channels))

    def run(self):
        time.sleep(1800)
        try:
            while True:
                for epg_method in self.epg_methods:
                    last_update_time = self.fhdhr.db.get_fhdhr_value("update_time", epg_method)
                    updatetheepg = False
                    if not last_update_time:
                        updatetheepg = True
                    elif time.time() >= (last_update_time + self.sleeptime[epg_method]):
                        updatetheepg = True
                    if updatetheepg:
                        self.fhdhr.api.get("%s&source=%s" % (self.epg_update_url, epg_method))
                time.sleep(1800)
        except KeyboardInterrupt:
            pass
