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

            clean_prog_dicts = self.empty_channel_epg(timestamps, chan_obj)
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
                time_start = datetime.datetime.combine(xdate, datetime.time(hour, 0))
                if hour + 1 < 24:
                    time_end = datetime.datetime.combine(xdate, datetime.time(hour + 1, 0))
                else:
                    time_end = datetime.datetime.combine(xtdate, datetime.time(0, 0))
                timestampdict = {
                                "time_start": str(time_start.strftime('%Y%m%d%H%M%S')) + " +0000",
                                "time_end": str(time_end.strftime('%Y%m%d%H%M%S')) + " +0000",
                                }
                timestamps.append(timestampdict)
        return timestamps

    def empty_channel_epg(self, timestamps, chan_obj):
        clean_prog_dicts = []
        for timestamp in timestamps:
            content_id = "%s_%s" % (chan_obj.dict["origin_id"], str(timestamp['time_start']).split(" ")[0])
            clean_prog_dict = {
                                "time_start": timestamp['time_start'],
                                "time_end": timestamp['time_end'],
                                "duration_minutes": 60,
                                "thumbnail": chan_obj.dict["thumbnail"] or self.get_content_thumbnail(content_id),
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
            clean_prog_dicts.append(clean_prog_dict)
        return clean_prog_dicts
