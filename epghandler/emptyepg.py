import os
import json
import datetime


class EmptyEPG():

    def __init__(self, config):

        self.config = config.config

        self.postalcode = None

        self.epg_cache = None
        self.cache_dir = config.config["main"]["empty_cache"]
        self.epg_cache_file = config.config["main"]["empty_cache_file"]
        self.epg_cache = self.epg_cache_open()

    def epg_cache_open(self):
        epg_cache = None
        if os.path.isfile(self.epg_cache_file):
            with open(self.epg_cache_file, 'r') as epgfile:
                epg_cache = json.load(epgfile)
        return epg_cache

    def update_epg(self):
        print('Updating Empty EPG cache file.')

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

        for c in self.serviceproxy.get_channels():
            if str(c["number"]) not in list(programguide.keys()):
                programguide[str(c["number"])] = {
                                                    "callsign": c["callsign"],
                                                    "name": c["name"],
                                                    "number": c["number"],
                                                    "id": c["id"],
                                                    "thumbnail": ("/images?source=empty&type=channel&id=%s" % (str(c['number']))),
                                                    "listing": [],
                                                    }

            for timestamp in timestamps:
                clean_prog_dict = {
                                    "time_start": timestamp['time_start'],
                                    "time_end": timestamp['time_end'],
                                    "duration_minutes": 60,
                                    "thumbnail": ("/images?source=empty&type=content&id=%s" % (str(c['number']))),
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
                                    "id": timestamp['time_start'],
                                    }

                programguide[str(c["number"])]["listing"].append(clean_prog_dict)

        self.epg_cache = programguide
        with open(self.empty_cache_file, 'w') as epgfile:
            epgfile.write(json.dumps(programguide, indent=4))
        print('Wrote updated Empty EPG cache file.')
        return programguide
