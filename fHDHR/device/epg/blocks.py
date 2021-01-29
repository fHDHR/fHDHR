import datetime


class blocksEPG():

    def __init__(self, fhdhr, channels, origins, origin):
        self.fhdhr = fhdhr
        self.channels = channels
        self.origins = origins
        self.origin = origin

    def update_epg(self):
        programguide = {}

        timestamps = self.timestamps

        for fhdhr_id in [x["id"] for x in self.channels.get_channels(self.origin)]:
            chan_obj = self.channels.get_channel_obj("id", fhdhr_id, self.origin)

            if str(chan_obj.number) not in list(programguide.keys()):
                programguide[str(chan_obj.number)] = chan_obj.epgdict

            clean_prog_dicts = self.empty_channel_epg(timestamps, chan_obj=chan_obj)
            for clean_prog_dict in clean_prog_dicts:
                programguide[str(chan_obj.number)]["listing"].append(clean_prog_dict)

        return programguide

    @property
    def timestamps(self):
        desired_start_time = (datetime.datetime.today() + datetime.timedelta(days=self.fhdhr.config.dict["epg"]["reverse_days"])).timestamp()
        desired_end_time = (datetime.datetime.today() + datetime.timedelta(days=self.fhdhr.config.dict["epg"]["forward_days"])).timestamp()
        return self.timestamps_between(desired_start_time, desired_end_time)

    def timestamps_between(self, starttime, endtime):
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
        clean_prog_dicts = []
        for timestampdict in timestamps:
            clean_prog_dict = self.single_channel_epg(timestampdict, chan_obj=chan_obj, chan_dict=chan_dict)
            clean_prog_dicts.append(clean_prog_dict)
        return clean_prog_dicts

    def empty_listing(self, chan_obj=None, chan_dict=None):
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
