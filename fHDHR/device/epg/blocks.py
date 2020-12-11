import datetime


class blocksEPG():

    def __init__(self, fhdhr, channels):
        self.fhdhr = fhdhr

        self.channels = channels

    def update_epg(self):
        programguide = {}

        timestamps = self.timestamps

        for fhdhr_id in list(self.channels.list.keys()):
            chan_obj = self.channels.list[fhdhr_id]

            if str(chan_obj.number) not in list(programguide.keys()):
                programguide[str(chan_obj.number)] = chan_obj.epgdict

            clean_prog_dicts = self.empty_channel_epg(timestamps, chan_obj=chan_obj)
            for clean_prog_dict in clean_prog_dicts:
                programguide[str(chan_obj.number)]["listing"].append(clean_prog_dict)

        return programguide

    def get_content_thumbnail(self, content_id):
        return "/api/images?method=generate&type=content&message=%s" % content_id

    @property
    def timestamps(self):
        timestamps = []
        todaydate = datetime.date.today()
        for x in range(0, 6):
            xdate = todaydate + datetime.timedelta(days=x)
            xtdate = xdate + datetime.timedelta(days=1)

            for hour in range(0, 24):
                time_start = datetime.datetime.combine(xdate, datetime.time(hour, 0)).timestamp()
                if hour + 1 < 24:
                    time_end = datetime.datetime.combine(xdate, datetime.time(hour + 1, 0)).timestamp()
                else:
                    time_end = datetime.datetime.combine(xtdate, datetime.time(0, 0)).timestamp()
                timestampdict = {
                                "time_start": time_start,
                                "time_end": time_end,
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
            clean_prog_dict["thumbnail"] = self.get_content_thumbnail(content_id)

        return clean_prog_dict

    def empty_channel_epg(self, timestamps, chan_obj=None, chan_dict=None):
        clean_prog_dicts = []
        for timestampdict in timestamps:
            clean_prog_dict = self.single_channel_epg(timestampdict, chan_obj=chan_obj, chan_dict=chan_dict)
            clean_prog_dicts.append(clean_prog_dict)
        return clean_prog_dicts

    def empty_listing(self):
        return {
                "time_start": None,
                "time_end": None,
                "duration_minutes": None,
                "thumbnail": None,
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
                "id": None,
            }
