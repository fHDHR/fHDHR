import json
import datetime
import urllib.request

import fHDHR.tools


class OriginEPG():

    def __init__(self, settings, logger, web):
        self.config = settings
        self.logger = logger
        self.web = web

        self.web_cache_dir = self.config.dict["filedir"]["epg_cache"]["origin"]["web_cache"]

    def update_epg(self, fhdhr_channels):
        programguide = {}

        # Make a date range to pull
        todaydate = datetime.date.today()
        dates_to_pull = [todaydate]
        for x in range(1, 6):
            xdate = todaydate + datetime.timedelta(days=x)
            dates_to_pull.append(xdate)

        self.remove_stale_cache(todaydate)

        for x_date in dates_to_pull:
            url = ('https://api.locastnet.org/api/watch/epg/' +
                   str(fhdhr_channels.origin.location["DMA"]) + "?startTime=" + str(x_date) + "T00%3A00%3A00-00%3A00")

            result = self.get_cached(str(x_date), url)
            d = json.loads(result)

            for c in d:

                cdict = fHDHR.tools.xmldictmaker(c, ["callSign", "name", "channelId"], list_items=[], str_items=[])

                channel_number = str(cdict['callSign']).split(" ")[0]

                if str(channel_number) not in list(programguide.keys()):
                    programguide[str(channel_number)] = {
                                                      "callsign": str(cdict['name']),
                                                      "name": str(cdict['callSign']).split(" ")[1],
                                                      "number": channel_number,
                                                      "id": str(cdict["id"]),
                                                      "thumbnail": str(cdict['logo226Url']),
                                                      "listing": [],
                                                      }

                for event in c['listings']:

                    eventdict = fHDHR.tools.xmldictmaker(event, ["startTime", "endTime", "duration", "preferredImage",
                                                                 "genres", "episodeTitle", "title", "sub-title",
                                                                 "entityType", "releaseYear", "description", "shortDescription",
                                                                 "rating", "isNew", "showType", "programId",
                                                                 "seasonNumber", "episodeNumber"], str_items=["genres"])

                    clean_prog_dict = {
                                    "time_start": self.locast_xmltime(eventdict['startTime']),
                                    "time_end": self.locast_xmltime((eventdict['startTime'] + (eventdict['duration'] * 1000))),
                                    "duration_minutes": eventdict['duration'] * 1000,
                                    "thumbnail": eventdict["preferredImage"],
                                    "title": eventdict['title'] or "Unavailable",
                                    "sub-title": eventdict['sub-title'] or "Unavailable",
                                    "description": eventdict['description'] or eventdict['shortDescription'] or "Unavailable",
                                    "rating": eventdict['rating'] or "N/A",
                                    "episodetitle": eventdict['episodeTitle'],
                                    "releaseyear": eventdict['releaseYear'],
                                    "genres": eventdict['genres'].split(","),
                                    "seasonnumber": eventdict['seasonNumber'],
                                    "episodenumber": eventdict['episodeNumber'],
                                    "isnew": eventdict['isNew'],
                                    "id": str(eventdict['programId'])
                                    }

                    if eventdict["entityType"] == "Movie" and clean_prog_dict['releaseyear']:
                        clean_prog_dict["sub-title"] = 'Movie: ' + str(clean_prog_dict['releaseyear'])
                    elif clean_prog_dict['episodetitle']:
                        clean_prog_dict["sub-title"] = clean_prog_dict['episodetitle']

                    if eventdict["showType"]:
                        clean_prog_dict["genres"].append(eventdict["showType"])
                    if eventdict["entityType"]:
                        clean_prog_dict["genres"].append(eventdict["entityType"])

                    programguide[str(channel_number)]["listing"].append(clean_prog_dict)

        return programguide

    def locast_xmltime(self, tm):
        tm = datetime.datetime.fromtimestamp(tm/1000.0)
        tm = str(tm.strftime('%Y%m%d%H%M%S')) + " +0000"
        return tm

    def get_cached(self, cache_key, url):
        cache_path = self.web_cache_dir.joinpath(cache_key)
        if cache_path.is_file():
            self.logger.info('FROM CACHE:  ' + str(cache_path))
            with open(cache_path, 'rb') as f:
                return f.read()
        else:
            self.logger.info('Fetching:  ' + url)
            try:
                resp = urllib.request.urlopen(url)
                result = resp.read()
            except urllib.error.HTTPError as e:
                if e.code == 400:
                    self.logger.info('Got a 400 error!  Ignoring it.')
                    result = (
                        b'{'
                        b'"note": "Got a 400 error at this time, skipping.",'
                        b'"channels": []'
                        b'}')
                else:
                    raise
            with open(cache_path, 'wb') as f:
                f.write(result)
            return result

    def remove_stale_cache(self, todaydate):
        for p in self.web_cache_dir.glob('*'):
            try:
                cachedate = datetime.datetime.strptime(str(p.name), "%Y-%m-%d")
                todaysdate = datetime.datetime.strptime(str(todaydate), "%Y-%m-%d")
                if cachedate >= todaysdate:
                    continue
            except Exception as e:
                self.logger.error(e)
                pass
            self.logger.info('Removing stale cache file:' + p.name)
            p.unlink()
