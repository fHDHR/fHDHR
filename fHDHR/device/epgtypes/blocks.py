import datetime


class blocksEPG():

    def __init__(self, fhdhr, channels):
        self.fhdhr = fhdhr

        self.channels = channels

    def update_epg(self):
        programguide = {}

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

        for c in self.channels.get_channels():
            if str(c["number"]) not in list(programguide.keys()):
                programguide[str(c["number"])] = {
                                                    "callsign": c["callsign"],
                                                    "name": c["name"],
                                                    "number": c["number"],
                                                    "id": c["origin_id"],
                                                    "thumbnail": ("/api/images?method=generate&type=channel&message=%s" % (str(c['number']))),
                                                    "listing": [],
                                                    }

            for timestamp in timestamps:
                clean_prog_dict = {
                                    "time_start": timestamp['time_start'],
                                    "time_end": timestamp['time_end'],
                                    "duration_minutes": 60,
                                    "thumbnail": ("/api/images?method=generate&type=content&message=%s" % (str(c["origin_id"]) + "_" + str(timestamp['time_start']).split(" ")[0])),
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
                                    "id": str(c["origin_id"]) + "_" + str(timestamp['time_start']).split(" ")[0],
                                    }

                programguide[str(c["number"])]["listing"].append(clean_prog_dict)

        return programguide
