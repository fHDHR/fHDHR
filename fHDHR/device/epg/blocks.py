import datetime
import time


class blocksEPG():
    """
    Blocks EPG Data for Origins missing EPG data.
    """

    def __init__(self, fhdhr, origins, origin_name):
        self.fhdhr = fhdhr
        self.origins = origins
        self.origin_name = origin_name

    """Functions/properties called During init"""

    @property
    def name(self):
        return "blocks"

    """Expected Properties for an EPG"""

    def update_epg(self):
        """
        Generate a full program guide without data.
        """

        programguide = {}

        timestamps = self.timestamps

        for fhdhr_channel_id in self.fhdhr.origins.origins_dict[self.origin_name].list_channel_ids:
            chan_obj = self.fhdhr.origins.origins_dict[self.origin_name].find_channel_obj(fhdhr_channel_id, searchkey="id")
            if chan_obj:

                if str(chan_obj.number) not in list(programguide.keys()):
                    programguide[str(chan_obj.number)] = chan_obj.epgdict

                clean_prog_dicts = self.empty_channel_epg(timestamps, chan_obj=chan_obj)
                for clean_prog_dict in clean_prog_dicts:
                    programguide[str(chan_obj.number)]["listing"].append(clean_prog_dict)

        return programguide

    @property
    def timestamps(self):
        """
        Generate timestamps for a star and end time for EPG data.
        """

        desired_start_time = (datetime.datetime.today() + datetime.timedelta(days=-abs(self.fhdhr.config.dict["epg"]["reverse_days"]))).timestamp()
        desired_end_time = (datetime.datetime.today() + datetime.timedelta(days=self.fhdhr.config.dict["epg"]["forward_days"])).timestamp()
        return self.timestamps_between(desired_start_time, desired_end_time)

    def timestamps_between(self, starttime, endtime):
        """
        Create Blocks of time between two times.
        """

        timestamps = []
        desired_blocksize = self.fhdhr.config.dict["epg"]["block_size"]
        current_time = starttime
        while (current_time + desired_blocksize) <= endtime:
            timestampdict = {
                            "time_start": current_time,
                            "time_end": current_time + desired_blocksize,
                            }
            timestamps.append(timestampdict)
            current_time += desired_blocksize
        if current_time < endtime:
            timestampdict = {
                            "time_start": current_time,
                            "time_end": endtime
                            }
            timestamps.append(timestampdict)
        return timestamps

    def single_channel_epg(self, timestampdict, chan_obj=None, chan_dict=None):
        """
        Generate EPG for a single Channel between timeslots.
        """

        if chan_obj:
            content_id = "%s_%s" % (chan_obj.dict["origin_id"], timestampdict['time_start'])
        elif chan_dict:
            content_id = "%s_%s" % (chan_dict["id"], timestampdict['time_start'])

        clean_prog_dict = {
                            "time_start": timestampdict['time_start'],
                            "time_end": timestampdict['time_end'],
                            "duration_minutes": (timestampdict['time_end'] - timestampdict['time_start']) / 60,
                            "title": "Unavailable",
                            "sub-title": "Unavailable",
                            "description": "Unavailable",
                            "rating": "N/A",
                            "episodetitle": None,
                            "releaseyear": None,
                            "genres": [],
                            "seasonnumber": None,
                            "episodenumber": None,
                            "isnew": False,
                            "id": content_id,
                            }
        if chan_obj:
            clean_prog_dict["thumbnail"] = chan_obj.thumbnail
        elif chan_dict:
            clean_prog_dict["thumbnail"] = chan_dict["thumbnail"]
        if not clean_prog_dict["thumbnail"]:
            clean_prog_dict["thumbnail"] = "/api/images?method=generate&type=content&message=%s" % content_id

        return clean_prog_dict

    def empty_channel_epg(self, timestamps, chan_obj=None, chan_dict=None):
        """
        Generate EPG for a channel.
        """

        clean_prog_dicts = []
        for timestampdict in timestamps:
            clean_prog_dict = self.single_channel_epg(timestampdict, chan_obj=chan_obj, chan_dict=chan_dict)
            clean_prog_dicts.append(clean_prog_dict)

        return clean_prog_dicts

    def empty_listing(self, chan_obj=None, chan_dict=None):
        """
        Create empty program info.
        """

        clean_prog_dict = {
                            "time_start": None,
                            "time_end": None,
                            "duration_minutes": None,
                            "title": "Unavailable",
                            "sub-title": "Unavailable",
                            "description": "Unavailable",
                            "rating": "N/A",
                            "episodetitle": None,
                            "releaseyear": None,
                            "genres": [],
                            "seasonnumber": None,
                            "episodenumber": None,
                            "isnew": False,
                            "id": "Unavailable",
                        }

        if chan_obj:
            clean_prog_dict["thumbnail"] = chan_obj.thumbnail

        elif chan_dict:
            clean_prog_dict["thumbnail"] = chan_dict["thumbnail"]

        else:
            clean_prog_dict["thumbnail"] = None

        if not clean_prog_dict["thumbnail"]:
            clean_prog_dict["thumbnail"] = "/api/images?method=generate&type=content&message=Unavailable"

        return clean_prog_dict

    @property
    def config_dict(self):
        return self.fhdhr.config.dict["epg"]

    """
    Returns configuration values in the following order
    1) If the plugin manually handles it
    2) The value we use in the config system
    """

    @property
    def update_frequency(self):
        return self.config_dict["update_frequency"]

    @property
    def xmltv_offset(self):
        return self.config_dict["xmltv_offset"]

    @property
    def epg_update_on_start(self):
        return self.config_dict["epg_update_on_start"]

    def clear_cache(self):
        self._epgdict = {}
        self.fhdhr.db.delete_fhdhr_value("epg_dict", self.name)

    def get_epg(self):

        if len(self._epgdict.keys()):
            return self._epgdict

        self._epgdict = self.fhdhr.db.get_fhdhr_value("epg_dict", self.name) or {}

    def set_epg(self, sorted_chan_guide):
        self._epgdict = sorted_chan_guide
        self.fhdhr.db.set_fhdhr_value("epg_dict", self.name, sorted_chan_guide)
        self.fhdhr.db.set_fhdhr_value("epg", "update_time", self.name, time.time())
