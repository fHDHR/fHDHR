import time
import datetime

from fHDHR.tools import channel_sort

from .blocks import blocksEPG


class EPG():
    """
    fHDHR EPG System.
    """

    def __init__(self, fhdhr, channels, origins):
        self.fhdhr = fhdhr

        self.fhdhr.logger.info("Initializing EPG system")

        self.origins = origins
        self.channels = channels

        self.blocks = blocksEPG(self.fhdhr, self.channels, self.origins, None)
        self.epg_handling = {}
        self.epg_method_selfadd()

        self.epg_update_url = "/api/epg?method=update"

        for epg_method in self.epg_methods:
            frequency_seconds = self.epg_handling[epg_method]["class"].update_frequency
            update_url = "%s&source=%s" % (self.epg_update_url, epg_method)
            self.fhdhr.scheduler.every(frequency_seconds).seconds.do(
                self.fhdhr.scheduler.job_wrapper(self.fhdhr.api.threadget), url=update_url).tag("%s EPG Update" % epg_method)

    @property
    def valid_epg_methods(self):
        """
        List of valid EPG methods.
        """

        return [x for x in list(self.epg_handling.keys())]

    @property
    def def_method(self):
        """
        The Default EPG method when unset.
        """

        epg_methods = self.epg_methods

        if not len(epg_methods):
            return None

        else:
            return epg_methods[0]

    @property
    def epg_methods(self):
        """
        List EPG methods.
        """

        epg_methods = []
        if not self.fhdhr.config.dict["epg"]["method"] or self.fhdhr.config.dict["epg"]["method"] in ["None"]:
            return []

        if isinstance(self.fhdhr.config.dict["epg"]["method"], str):
            self.fhdhr.config.dict["epg"]["method"] = [self.fhdhr.config.dict["epg"]["method"]]

        for epg_method in self.fhdhr.config.dict["epg"]["method"]:

            if epg_method in self.valid_epg_methods:
                epg_methods.append(epg_method)

            elif epg_method in [origin for origin in list(self.origins.origins_dict.keys())]:
                epg_methods.append(epg_method)

            elif epg_method in ["origin", "origins"]:
                epg_methods.extend([origin for origin in list(self.origins.origins_dict.keys())])

        return epg_methods

    def delete_channel(self, fhdhr_id, origin):
        """
        Delete Channel match.
        """

        for method in self.epg_methods:

            epg_chan_matches = self.fhdhr.db.get_fhdhr_value("epg_channels", "list", method) or {}
            for epg_chan_id in list(epg_chan_matches.keys()):

                if epg_chan_matches[epg_chan_id]["epg_chan_id"] == origin and epg_chan_matches[epg_chan_id]["fhdhr_id"] == fhdhr_id:
                    del epg_chan_matches[epg_chan_id]

            self.fhdhr.db.set_fhdhr_value("epg_channels", "list", epg_chan_matches, method)

    def get_epg_chan_match(self, method, epg_chan_id):
        """
        Get EPG Channel Match.
        """

        epg_chan_matches = self.fhdhr.db.get_fhdhr_value("epg_channels", "list", method) or {}

        if epg_chan_id in list(epg_chan_matches.keys()):
            return epg_chan_matches[epg_chan_id]

        return None

    def get_epg_chan_unmatched(self, origin, method):
        """
        Get Unmatched Channels.
        """

        unmatch_dicts = []
        origin_matches = [x["fhdhr_id"] for x in self.get_origin_matches(origin, method)]
        for fhdhr_id in [x["id"] for x in self.channels.get_channels(origin)]:

            chan_obj = self.channels.get_channel_obj("id", fhdhr_id, origin)
            if chan_obj:

                if chan_obj.dict["id"] not in origin_matches:
                    unmatch_dicts.append({
                                        "id": chan_obj.dict["id"],
                                        "number": chan_obj.number,
                                        "name": chan_obj.dict["name"],
                                        })

        return unmatch_dicts

    def get_origin_matches(self, origin, method):
        """
        Get EPG Origin Matches.
        """

        matches = []
        epg_chan_matches = self.fhdhr.db.get_fhdhr_value("epg_channels", "list", method) or {}
        for epg_chan_id in list(epg_chan_matches.keys()):

            if epg_chan_matches[epg_chan_id]["origin"] == origin:
                matches.append(epg_chan_matches[epg_chan_id])

        return matches

    def set_epg_chan_match(self, method, epg_chan_id, fhdhr_id, origin):
        """
        Set EPG Channel Match.
        """

        epg_chan_matches = self.fhdhr.db.get_fhdhr_value("epg_channels", "list", method) or {}
        epg_chan_matches[epg_chan_id] = {
                                         "fhdhr_id": fhdhr_id,
                                         "origin": origin
                                         }

        self.fhdhr.db.set_fhdhr_value("epg_channels", "list", epg_chan_matches, method)

    def unset_epg_chan_match(self, method, epg_chan_id):
        """
        Unset EPG Channel Match.
        """

        epg_chan_matches = self.fhdhr.db.get_fhdhr_value("epg_channels", "list", method) or {}
        if epg_chan_id in list(epg_chan_matches.keys()):
            del epg_chan_matches[epg_chan_id]

        self.fhdhr.db.set_fhdhr_value("epg_channels", "list", epg_chan_matches, method)

    def clear_epg_cache(self, method=None):
        """
        Clear EPG Cache.
        """

        if not method:

            if not self.def_method:
                return

        if method not in self.valid_epg_methods:

            if not self.def_method:
                return

            method = self.def_method

        self.fhdhr.logger.info("Clearing %s EPG cache." % method)

        if hasattr(self.epg_handling[method]["class"], 'clear_cache'):
            self.epg_handling[method]["class"].clear_cache()

        if method in list(self.epg_handling.keys()):

            if "epgdict" in list(self.epg_handling[method].keys()):
                del self.epg_handling[method]["epgdict"]

        self.fhdhr.db.delete_fhdhr_value("epg_dict", method)

    def whats_on_now(self, channel_number, method=None, chan_obj=None, chan_dict=None):
        """
        Find what is currently ON a channel, via EPG.
        """

        nowtime = time.time()
        epgdict = self.get_epg(method)

        if channel_number not in list(epgdict.keys()):
            epgdict[channel_number] = {
                                        "callsign": "",
                                        "name": "",
                                        "number": str(channel_number),
                                        "id": "",
                                        "thumbnail": "",
                                        "listing": []
                                        }

        for listing in epgdict[channel_number]["listing"]:

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
        """
        Find what is currently ON all channels, via EPG.
        """

        if not method:

            if not self.def_method:
                return

            method = self.def_method

        if method not in self.valid_epg_methods:

            if not self.def_method:
                return

            method = self.def_method

        channel_guide_dict = {}
        epgdict = self.get_epg(method)
        epgdict = epgdict.copy()

        for c in list(epgdict.keys()):

            if method in [origin for origin in list(self.origins.origins_dict.keys())]:

                chan_obj = self.channels.get_channel_obj("origin_id", epgdict[c]["id"])
                if chan_obj:
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

            else:
                chan_obj = None
                channel_number = c

            whatson = self.whats_on_now(channel_number, method, chan_dict=epgdict, chan_obj=chan_obj)
            if whatson:
                channel_guide_dict[channel_number] = whatson

        return channel_guide_dict

    def get_epg(self, method=None):
        """
        Get EPG from EPG Method
        """

        if not method:

            if not self.def_method:
                return

            method = self.def_method

        if method not in self.valid_epg_methods:

            if not self.def_method:
                return

            method = self.def_method

        if method in list(self.epg_handling.keys()):

            if "epgdict" in list(self.epg_handling[method].keys()):
                return self.epg_handling[method]["epgdict"]

        self.update(method)
        self.epg_handling[method]["epgdict"] = self.fhdhr.db.get_fhdhr_value("epg_dict", method) or {}

        return self.epg_handling[method]["epgdict"]

    def get_thumbnail(self, itemtype, itemid):
        """
        Get EPG Thumbnail URL.
        """

        if itemtype == "channel":
            chandict = self.find_channel_dict(itemid)
            return chandict["thumbnail"]

        elif itemtype == "content":
            progdict = self.find_program_dict(itemid)
            return progdict["thumbnail"]

        return None

    def find_channel_dict(self, channel_id):
        """
        Find Channel dict.
        """

        epgdict = self.get_epg()
        channel_list = [epgdict[x] for x in list(epgdict.keys())]

        for item in channel_list:

            if item["id"] == channel_id:
                return item

        return None

    def find_program_dict(self, event_id):
        """
        Find Program dict.
        """

        epgdict = self.get_epg()
        event_list = []

        for channel in list(epgdict.keys()):
            event_list.extend(epgdict[channel]["listing"])

        for item in event_list:

            if item["id"] == event_id:
                return item

        return None

    def epg_method_selfadd(self):
        """
        Add EPG methods.
        """

        self.fhdhr.logger.info("Detecting and Opening any found EPG plugins.")
        for plugin_name in list(self.fhdhr.plugins.plugins.keys()):

            if self.fhdhr.plugins.plugins[plugin_name].type == "alt_epg":
                method = self.fhdhr.plugins.plugins[plugin_name].name.lower()
                self.epg_handling[method] = {
                                            "class": self.fhdhr.plugins.plugins[plugin_name].Plugin_OBJ(self.channels, self.fhdhr.plugins.plugins[plugin_name].plugin_utils)
                                            }

        for origin in list(self.origins.origins_dict.keys()):

            if origin.lower() not in list(self.epg_handling.keys()):
                self.fhdhr.logger.debug("Creating Blocks EPG for %s." % origin)
                self.epg_handling[origin.lower()] = {
                                                    "class": blocksEPG(self.fhdhr, self.channels, self.origins, origin)
                                                    }

                self.valid_epg_methods.append(origin.lower())

        for epg_method in list(self.epg_handling.keys()):

            if not hasattr(self.epg_handling[epg_method]["class"], 'update_frequency'):
                update_frequency = self.fhdhr.config.dict["epg"]["update_frequency"]
                if epg_method in list(self.fhdhr.config.dict.keys()):
                    if "update_frequency" in list(self.fhdhr.config.dict[epg_method].keys()):
                        update_frequency = self.fhdhr.config.dict[epg_method]["update_frequency"]
                self.fhdhr.logger.debug("Setting %s update_frequency to: %s" % (epg_method, update_frequency))
                self.epg_handling[epg_method]["class"].update_frequency = update_frequency

            if not hasattr(self.epg_handling[epg_method]["class"], 'xmltv_offset'):
                xmltv_offset = self.fhdhr.config.dict["epg"]["xmltv_offset"]
                if epg_method in list(self.fhdhr.config.dict.keys()):
                    if "xmltv_offset" in list(self.fhdhr.config.dict[epg_method].keys()):
                        xmltv_offset = self.fhdhr.config.dict[epg_method]["xmltv_offset"]
                self.fhdhr.logger.debug("Setting %s xmltv_offset to: %s" % (epg_method, xmltv_offset))
                self.epg_handling[epg_method]["class"].xmltv_offset = xmltv_offset

            if not hasattr(self.epg_handling[epg_method]["class"], 'epg_update_on_start'):
                epg_update_on_start = self.fhdhr.config.dict["epg"]["epg_update_on_start"]
                if epg_method in list(self.fhdhr.config.dict.keys()):
                    if "epg_update_on_start" in list(self.fhdhr.config.dict[epg_method].keys()):
                        epg_update_on_start = self.fhdhr.config.dict[epg_method]["epg_update_on_start"]
                self.fhdhr.logger.debug("Setting %s epg_update_on_start to: %s" % (epg_method, epg_update_on_start))
                self.epg_handling[epg_method]["class"].epg_update_on_start = epg_update_on_start

    def update(self, method=None):
        """
        Update EPG data.
        """

        if not method:

            if not self.def_method:
                return

            method = self.def_method

        if method not in self.valid_epg_methods:

            if not self.def_method:
                return

            method = self.def_method

        self.fhdhr.logger.noob("Updating %s EPG cache." % method)
        programguide = self.epg_handling[method]["class"].update_epg()

        # sort the channel listings by time stamp
        for cnum in list(programguide.keys()):
            programguide[cnum]["listing"] = sorted(programguide[cnum]["listing"], key=lambda i: i['time_start'])

        # Gernate Block periods for between EPG data, if missing
        clean_prog_guide = {}
        desired_start_time = (datetime.datetime.today() + datetime.timedelta(days=-abs(self.fhdhr.config.dict["epg"]["reverse_days"]))).timestamp()
        desired_end_time = (datetime.datetime.today() + datetime.timedelta(days=self.fhdhr.config.dict["epg"]["forward_days"])).timestamp()
        for cnum in list(programguide.keys()):

            if cnum not in list(clean_prog_guide.keys()):
                clean_prog_guide[cnum] = programguide[cnum].copy()
                clean_prog_guide[cnum]["listing"] = []

            if method in [origin for origin in list(self.origins.origins_dict.keys())]:
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
        if method in [origin for origin in list(self.origins.origins_dict.keys())]:

            timestamps = self.blocks.timestamps
            for fhdhr_id in [x["id"] for x in self.channels.get_channels(method)]:

                chan_obj = self.channels.get_channel_obj("id", fhdhr_id, method)
                if chan_obj:

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

        self.epg_handling[method]["epgdict"] = sorted_chan_guide
        self.fhdhr.db.set_fhdhr_value("epg_dict", method, programguide)
        self.fhdhr.db.set_fhdhr_value("epg", "update_time", method, time.time())
        self.fhdhr.logger.noob("Wrote %s EPG cache. %s Programs for %s Channels" % (method, total_programs, total_channels))
