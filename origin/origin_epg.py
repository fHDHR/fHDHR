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

        url = "https://api.locastnet.org/api/watch/epg/%s" % fhdhr_channels.origin.location["DMA"]
        url_headers = {'Content-Type': 'application/json', 'authorization': 'Bearer %s' % fhdhr_channels.origin.token}
        self.fhdhr.logger.info("Fetching:  %s" % url)
        try:
            resp = self.fhdhr.web.session.get(url, headers=url_headers)
            uncached_result = resp.json()
        except self.fhdhr.web.exceptions.SSLError:
            self.fhdhr.logger.info('Got an error!  Ignoring it.')
            uncached_result = {}
        except self.fhdhr.web.exceptions.HTTPError:
            self.fhdhr.logger.info('Got an error!  Ignoring it.')
            uncached_result = {}

        cached_items = self.get_cached(dates_to_pull, fhdhr_channels.origin.location["DMA"])
        cached_items.insert(0, uncached_result)
        for result in cached_items:

            for c in result:

                chan_obj = fhdhr_channels.get_channel_obj("origin_id", c["id"])

                if str(chan_obj.number) not in list(programguide.keys()):
                    programguide[str(chan_obj.number)] = chan_obj.epgdict

                for event in c['listings']:

                    eventdict = fHDHR.tools.xmldictmaker(event, ["startTime", "endTime", "duration", "preferredImage",
                                                                 "genres", "episodeTitle", "title", "sub-title",
                                                                 "entityType", "releaseYear", "description", "shortDescription",
                                                                 "rating", "isNew", "showType", "programId",
                                                                 "seasonNumber", "episodeNumber"], str_items=["genres"])

                    timestamp = self.locast_timestamps(eventdict['startTime'], eventdict['duration'])

                    clean_prog_dict = {
                                    "time_start": timestamp['time_start'],
                                    "time_end": timestamp['time_end'],
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
                        clean_prog_dict["sub-title"] = "Movie: %s" % clean_prog_dict['releaseyear']
                    elif clean_prog_dict['episodetitle']:
                        clean_prog_dict["sub-title"] = clean_prog_dict['episodetitle']

                    if eventdict["showType"]:
                        clean_prog_dict["genres"].append(eventdict["showType"])
                    if eventdict["entityType"]:
                        clean_prog_dict["genres"].append(eventdict["entityType"])

                    if not any((d['time_start'] == clean_prog_dict['time_start'] and d['id'] == clean_prog_dict['id']) for d in programguide[str(chan_obj.number)]["listing"]):
                        programguide[str(chan_obj.number)]["listing"].append(clean_prog_dict)

        return programguide

    def locast_timestamps(self, starttime, duration):
        starttime /= 1000
        endtime = starttime + duration
        timestamp = {
                    "time_start": starttime,
                    "time_end": endtime
                    }
        return timestamp

    def get_cached(self, dates_to_pull, dma):
        for x_date in dates_to_pull:
            url = 'https://api.locastnet.org/api/watch/epg/%s?startTime=%s%s' % (dma, x_date, "T00%3A00%3A00-00%3A00")
            self.get_cached_item(str(x_date), url)
        cache_list = self.fhdhr.db.get_cacheitem_value("cache_list", "epg_cache", "origin") or []
        return [self.fhdhr.db.get_cacheitem_value(x, "epg_cache", "origin") for x in cache_list]

    def get_cached_item(self, cache_key, url):
        cacheitem = self.fhdhr.db.get_cacheitem_value(cache_key, "epg_cache", "origin")
        if cacheitem:
            self.fhdhr.logger.info("FROM CACHE:  %s" % cache_key)
            return cacheitem
        else:
            self.fhdhr.logger.info("Fetching:  %s" % url)
            try:
                resp = self.fhdhr.web.session.get(url)
            except self.fhdhr.web.exceptions.HTTPError:
                self.fhdhr.logger.info('Got an error!  Ignoring it.')
                return
            result = resp.json()

            self.fhdhr.db.set_cacheitem_value(cache_key, "epg_cache", result, "origin")
            cache_list = self.fhdhr.db.get_cacheitem_value("cache_list", "epg_cache", "origin") or []
            cache_list.append(cache_key)
            self.fhdhr.db.set_cacheitem_value("cache_list", "epg_cache", cache_list, "origin")

    def remove_stale_cache(self, todaydate):
        cache_list = self.fhdhr.db.get_cacheitem_value("cache_list", "epg_cache", "origin") or []
        cache_to_kill = []
        for cacheitem in cache_list:
            cachedate = datetime.datetime.strptime(str(cacheitem), "%Y-%m-%d")
            todaysdate = datetime.datetime.strptime(str(todaydate), "%Y-%m-%d")
            if cachedate < todaysdate:
                cache_to_kill.append(cacheitem)
                self.fhdhr.db.delete_cacheitem_value(cacheitem, "epg_cache", "origin")
                self.fhdhr.logger.info("Removing stale cache:  %s" % cacheitem)
        self.fhdhr.db.set_cacheitem_value("cache_list", "epg_cache", [x for x in cache_list if x not in cache_to_kill], "origin")

    def clear_cache(self):
        cache_list = self.fhdhr.db.get_cacheitem_value("cache_list", "epg_cache", "origin") or []
        for cacheitem in cache_list:
            self.fhdhr.db.delete_cacheitem_value(cacheitem, "epg_cache", "origin")
            self.fhdhr.logger.info("Removing cache:  %s" % cacheitem)
        self.fhdhr.db.delete_cacheitem_value("cache_list", "epg_cache", "origin")
