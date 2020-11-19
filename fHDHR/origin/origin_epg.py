import datetime

import fHDHR.tools


class OriginEPG():

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def update_epg(self, fhdhr_channels):
        programguide = {}

        # Make a date range to pull
        todaydate = datetime.date.today()
        dates_to_pull = [todaydate]
        for x in range(1, 6):
            xdate = todaydate + datetime.timedelta(days=x)
            dates_to_pull.append(xdate)

        self.remove_stale_cache(todaydate)

        cached_items = self.get_cached(dates_to_pull, fhdhr_channels.origin.location["DMA"])
        for result in cached_items:

            for c in result:

                cdict = fHDHR.tools.xmldictmaker(c, ["callSign", "name", "channelId"], list_items=[], str_items=[])

                # Typically this will be `2.1 KTTW` but occasionally Locast only provides a channel number here
                # fHDHR device.channels will provide us a number if that is the case
                if (fHDHR.tools.isint(str(cdict['callSign']).split(" ")[0])
                   or fHDHR.tools.isfloat(str(cdict['callSign']).split(" ")[0])):
                    channel_number = str(cdict['callSign']).split(" ")[0]
                    channel_callsign = str(" ".join(cdict['callSign'].split(" ")[1:]))
                else:
                    channel_callsign = str(c['callSign'])
                    channel_number = fhdhr_channels.get_channel_dict("callsign", channel_callsign)["number"]

                if str(channel_number) not in list(programguide.keys()):
                    programguide[str(channel_number)] = {
                                                      "callsign": str(cdict['name']),
                                                      "name": channel_callsign,
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

                    if not any(d['id'] == clean_prog_dict['id'] for d in programguide[str(channel_number)]["listing"]):
                        programguide[str(channel_number)]["listing"].append(clean_prog_dict)

        return programguide

    def locast_xmltime(self, tm):
        tm = datetime.datetime.fromtimestamp(tm/1000.0)
        tm = str(tm.strftime('%Y%m%d%H%M%S')) + " +0000"
        return tm

    def get_cached(self, dates_to_pull, dma):
        for x_date in dates_to_pull:
            url = ('https://api.locastnet.org/api/watch/epg/' +
                   str(dma) + "?startTime=" + str(x_date) + "T00%3A00%3A00-00%3A00")
            self.get_cached_item(str(x_date), url)
        cache_list = self.fhdhr.db.get_cacheitem_value("cache_list", "offline_cache", "origin") or []
        return [self.fhdhr.db.get_cacheitem_value(x, "offline_cache", "origin") for x in cache_list]

    def get_cached_item(self, cache_key, url):
        cacheitem = self.fhdhr.db.get_cacheitem_value(cache_key, "offline_cache", "origin")
        if cacheitem:
            self.fhdhr.logger.info('FROM CACHE:  ' + str(cache_key))
            return cacheitem
        else:
            self.fhdhr.logger.info('Fetching:  ' + url)
            try:
                resp = self.fhdhr.web.session.get(url)
            except self.fhdhr.web.exceptions.HTTPError:
                self.fhdhr.logger.info('Got an error!  Ignoring it.')
                return
            result = resp.json()

            self.fhdhr.db.set_cacheitem_value(cache_key, "offline_cache", result, "origin")
            cache_list = self.fhdhr.db.get_cacheitem_value("cache_list", "offline_cache", "origin") or []
            cache_list.append(cache_key)
            self.fhdhr.db.set_cacheitem_value("cache_list", "offline_cache", cache_list, "origin")

    def remove_stale_cache(self, todaydate):
        cache_list = self.fhdhr.db.get_cacheitem_value("cache_list", "offline_cache", "origin") or []
        cache_to_kill = []
        for cacheitem in cache_list:
            cachedate = datetime.datetime.strptime(str(cacheitem), "%Y-%m-%d")
            todaysdate = datetime.datetime.strptime(str(todaydate), "%Y-%m-%d")
            if cachedate < todaysdate:
                cache_to_kill.append(cacheitem)
                self.fhdhr.db.delete_cacheitem_value(cacheitem, "offline_cache", "origin")
                self.fhdhr.logger.info('Removing stale cache:  ' + str(cacheitem))
        self.fhdhr.db.set_cacheitem_value("cache_list", "offline_cache", [x for x in cache_list if x not in cache_to_kill], "origin")

    def clear_cache(self):
        cache_list = self.fhdhr.db.get_cacheitem_value("cache_list", "offline_cache", "origin") or []
        for cacheitem in cache_list:
            self.fhdhr.db.delete_cacheitem_value(cacheitem, "offline_cache", "origin")
            self.fhdhr.logger.info('Removing cache:  ' + str(cacheitem))
        self.fhdhr.db.delete_cacheitem_value("cache_list", "offline_cache", "origin")
