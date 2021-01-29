import datetime

import fHDHR.tools


class Plugin_OBJ():

    def __init__(self, channels, plugin_utils):
        self.plugin_utils = plugin_utils

        self.channels = channels

        self.origin = plugin_utils.origin

    def update_epg(self):
        programguide = {}

        # Make a date range to pull
        todaydate = datetime.date.today()
        dates_to_pull = [todaydate]
        for x in range(1, 6):
            xdate = todaydate + datetime.timedelta(days=x)
            dates_to_pull.append(xdate)

        self.remove_stale_cache(todaydate)

        url = "https://api.locastnet.org/api/watch/epg/%s" % self.origin.location["DMA"]
        url_headers = {'Content-Type': 'application/json', 'authorization': 'Bearer %s' % self.origin.token}
        self.plugin_utils.logger.info("Fetching:  %s" % url)
        try:
            resp = self.plugin_utils.web.session.get(url, headers=url_headers)
            uncached_result = resp.json()
        except self.plugin_utils.web.exceptions.SSLError:
            self.plugin_utils.logger.info('Got an error!  Ignoring it.')
            uncached_result = {}
        except self.plugin_utils.web.exceptions.HTTPError:
            self.plugin_utils.logger.info('Got an error!  Ignoring it.')
            uncached_result = {}

        cached_items = self.get_cached(dates_to_pull, self.origin.location["DMA"])
        cached_items.insert(0, uncached_result)
        for result in cached_items:

            for c in result:

                chan_obj = self.channels.get_channel_obj("origin_id", c["id"], self.plugin_utils.namespace)

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
        cache_list = self.plugin_utils.db.get_plugin_value("cache_list", "epg_cache", "locast") or []
        return [self.plugin_utils.db.get_plugin_value(x, "epg_cache", "locast") for x in cache_list]

    def get_cached_item(self, cache_key, url):
        cacheitem = self.plugin_utils.db.get_plugin_value(cache_key, "epg_cache", "locast")
        if cacheitem:
            self.plugin_utils.logger.info("FROM CACHE:  %s" % cache_key)
            return cacheitem
        else:
            self.plugin_utils.logger.info("Fetching:  %s" % url)
            try:
                resp = self.plugin_utils.web.session.get(url)
            except self.plugin_utils.web.exceptions.HTTPError:
                self.plugin_utils.logger.info('Got an error!  Ignoring it.')
                return
            result = resp.json()

            self.plugin_utils.db.set_plugin_value(cache_key, "epg_cache", result, "locast")
            cache_list = self.plugin_utils.db.get_plugin_value("cache_list", "epg_cache", "locast") or []
            cache_list.append(cache_key)
            self.plugin_utils.db.set_plugin_value("cache_list", "epg_cache", cache_list, "locast")

    def remove_stale_cache(self, todaydate):
        cache_list = self.plugin_utils.db.get_plugin_value("cache_list", "epg_cache", "locast") or []
        cache_to_kill = []
        for cacheitem in cache_list:
            cachedate = datetime.datetime.strptime(str(cacheitem), "%Y-%m-%d")
            todaysdate = datetime.datetime.strptime(str(todaydate), "%Y-%m-%d")
            if cachedate < todaysdate:
                cache_to_kill.append(cacheitem)
                self.plugin_utils.db.delete_plugin_value(cacheitem, "epg_cache", "locast")
                self.plugin_utils.logger.info("Removing stale cache:  %s" % cacheitem)
        self.plugin_utils.db.set_plugin_value("cache_list", "epg_cache", [x for x in cache_list if x not in cache_to_kill], "locast")

    def clear_cache(self):
        cache_list = self.plugin_utils.db.get_plugin_value("cache_list", "epg_cache", "locast") or []
        for cacheitem in cache_list:
            self.plugin_utils.db.delete_plugin_value(cacheitem, "epg_cache", "locast")
            self.plugin_utils.logger.info("Removing cache:  %s" % cacheitem)
        self.plugin_utils.db.delete_plugin_value("cache_list", "epg_cache", "locast")
