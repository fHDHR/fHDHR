import datetime

from fHDHR.exceptions import EPGSetupError


class Plugin_OBJ():

    def __init__(self, channels, plugin_utils):
        self.plugin_utils = plugin_utils

        self.channels = channels

    @property
    def postalcode(self):
        if self.plugin_utils.config.dict["tvtv"]["postalcode"]:
            return self.plugin_utils.config.dict["tvtv"]["postalcode"]
        try:
            postalcode_url = 'http://ipinfo.io/json'
            postalcode_req = self.plugin_utils.web.session.get(postalcode_url)
            data = postalcode_req.json()
            postalcode = data["postal"]
        except Exception as e:
            raise EPGSetupError("Unable to automatically optain postalcode: %s" % e)
            postalcode = None
        return postalcode

    @property
    def lineup_id(self):
        lineup_id_url = "https://www.tvtv.us/tvm/t/tv/v4/lineups?postalCode=%s" % self.postalcode
        if self.plugin_utils.config.dict["tvtv"]["lineuptype"]:
            lineup_id_url += "&lineupType=%s" % self.plugin_utils.config.dict["tvtv"]["lineuptype"]
        lineup_id_req = self.plugin_utils.web.session.get(lineup_id_url)
        data = lineup_id_req.json()
        lineup_id = data[0]["lineupID"]
        return lineup_id

    def update_epg(self):
        programguide = {}

        # Make a date range to pull
        todaydate = datetime.date.today()
        dates_to_pull = []
        for x in range(-1, 6):
            datesdict = {
                        "start": todaydate + datetime.timedelta(days=x),
                        "stop": todaydate + datetime.timedelta(days=x+1)
                        }
            dates_to_pull.append(datesdict)

        self.remove_stale_cache(todaydate)

        cached_items = self.get_cached(dates_to_pull)
        for result in cached_items:

            for chan_item in result:

                channel_number = "%s.%s" % (chan_item["channel"]['channelNumber'], chan_item["channel"]['subChannelNumber'])

                if str(channel_number) not in list(programguide.keys()):

                    programguide[channel_number] = {
                                                        "callsign": chan_item["channel"]["callsign"],
                                                        "name": chan_item["channel"]["name"],
                                                        "number": channel_number,
                                                        "id": str(chan_item["channel"]["stationID"]),
                                                        "thumbnail": None,
                                                        "listing": [],
                                                        }
                    if chan_item["channel"]["logoFilename"]:
                        programguide[channel_number]["thumbnail"] = "https://cdn.tvpassport.com/image/station/100x100/%s" % chan_item["channel"]["logoFilename"]

                for listing in chan_item["listings"]:

                    timestamp = self.tvtv_timestamps(listing["listDateTime"], listing["duration"])

                    clean_prog_dict = {
                                        "time_start": timestamp['time_start'],
                                        "time_end": timestamp['time_end'],
                                        "duration_minutes": listing["duration"],
                                        "thumbnail": None,
                                        "title": listing["showName"],
                                        "sub-title": listing["episodeTitle"],
                                        "description": listing["description"],
                                        "rating": listing["rating"],
                                        "episodetitle": listing["episodeTitle"],
                                        "releaseyear": listing["year"],
                                        "genres": [],
                                        "seasonnumber": None,
                                        "episodenumber": None,
                                        "isnew": listing["new"],
                                        "id": listing["listingID"],
                                        }

                    if listing["artwork"]["poster"]:
                        listing["artwork"]["poster"] = "https://cdn.tvpassport.com/image/show/480x720/%s" % listing["artwork"]["poster"]

                    if not any((d['time_start'] == clean_prog_dict['time_start'] and d['id'] == clean_prog_dict['id']) for d in programguide[channel_number]["listing"]):
                        programguide[channel_number]["listing"].append(clean_prog_dict)

        return programguide

    def tvtv_timestamps(self, starttime, duration):
        start_time = datetime.datetime.strptime(starttime, '%Y-%m-%d %H:%M:%S').timestamp()
        timestamp = {
                    "time_start": start_time,
                    "time_end": start_time + (duration * 60)
                    }
        return timestamp

    def get_cached(self, dates_to_pull):
        for datesdict in dates_to_pull:
            starttime = "%s%s" % (datesdict["start"], "T00%3A00%3A00.000Z")
            stoptime = "%s%s" % (datesdict["stop"], "T00%3A00%3A00.000Z")
            url = "https://www.tvtv.us/tvm/t/tv/v4/lineups/%s/listings/grid?start=%s&end=%s" % (self.lineup_id, starttime, stoptime)
            self.get_cached_item(str(datesdict["start"]), url)
        cache_list = self.plugin_utils.db.get_plugin_value("cache_list", "epg_cache", "tvtv") or []
        return [self.plugin_utils.db.get_plugin_value(x, "epg_cache", "tvtv") for x in cache_list]

    def get_cached_item(self, cache_key, url):
        cacheitem = self.plugin_utils.db.get_plugin_value(cache_key, "epg_cache", "tvtv")
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

            self.plugin_utils.db.set_plugin_value(cache_key, "epg_cache", result, "tvtv")
            cache_list = self.plugin_utils.db.get_plugin_value("cache_list", "epg_cache", "tvtv") or []
            cache_list.append(cache_key)
            self.plugin_utils.db.set_plugin_value("cache_list", "epg_cache", cache_list, "tvtv")

    def remove_stale_cache(self, todaydate):
        cache_list = self.plugin_utils.db.get_plugin_value("cache_list", "epg_cache", "tvtv") or []
        cache_to_kill = []
        for cacheitem in cache_list:
            cachedate = datetime.datetime.strptime(str(cacheitem), "%Y-%m-%d")
            todaysdate = datetime.datetime.strptime(str(todaydate), "%Y-%m-%d")
            if cachedate < todaysdate:
                cache_to_kill.append(cacheitem)
                self.plugin_utils.db.delete_plugin_value(cacheitem, "epg_cache", "tvtv")
                self.plugin_utils.logger.info("Removing stale cache:  %s" % cacheitem)
        self.plugin_utils.db.set_plugin_value("cache_list", "epg_cache", [x for x in cache_list if x not in cache_to_kill], "tvtv")

    def clear_cache(self):
        cache_list = self.plugin_utils.db.get_plugin_value("cache_list", "epg_cache", "tvtv") or []
        for cacheitem in cache_list:
            self.plugin_utils.db.delete_plugin_value(cacheitem, "epg_cache", "tvtv")
            self.plugin_utils.logger.info("Removing cache:  %s" % str(cacheitem))
        self.plugin_utils.db.delete_plugin_value("cache_list", "epg_cache", "tvtv")
