import datetime
import urllib.parse

from fHDHR.tools import xmldictmaker
from fHDHR.exceptions import EPGSetupError


class Plugin_OBJ():

    def __init__(self, channels, plugin_utils):
        self.plugin_utils = plugin_utils

        self.channels = channels

    @property
    def postalcode(self):
        if self.plugin_utils.config.dict["zap2it"]["postalcode"]:
            return self.plugin_utils.config.dict["zap2it"]["postalcode"]
        try:
            postalcode_url = 'http://ipinfo.io/json'
            postalcode_req = self.plugin_utils.web.session.get(postalcode_url)
            data = postalcode_req.json()
            postalcode = data["postal"]
        except Exception as e:
            raise EPGSetupError("Unable to automatically optain postalcode: %s" % e)
            postalcode = None
        return postalcode

    def update_epg(self):
        programguide = {}

        # Start time parameter is now rounded down to nearest `zap_timespan`, in s.
        zap_time = datetime.datetime.utcnow().timestamp()
        self.remove_stale_cache(zap_time)
        zap_time_window = int(self.plugin_utils.config.dict["zap2it"]["timespan"]) * 3600
        zap_time = int(zap_time - (zap_time % zap_time_window))

        # Fetch data in `zap_timespan` chunks.
        i_times = []
        for i in range(int(7 * 24 / int(self.plugin_utils.config.dict["zap2it"]["timespan"]))):
            i_times.append(zap_time + (i * zap_time_window))

        cached_items = self.get_cached(i_times)
        for result in cached_items:

            for c in result['channels']:

                cdict = xmldictmaker(c, ["callSign", "name", "channelNo", "channelId", "thumbnail"])

                if str(cdict['channelNo']) not in list(programguide.keys()):

                    programguide[str(cdict['channelNo'])] = {
                                                        "callsign": cdict["callSign"],
                                                        "name": cdict["name"] or cdict["callSign"],  # TODO
                                                        "number": str(cdict["channelNo"]),
                                                        "id": str(cdict["channelId"]),
                                                        "thumbnail": str(cdict['thumbnail']).replace("//", "https://").split("?")[0],
                                                        "listing": [],
                                                        }

                for event in c['events']:

                    eventdict = xmldictmaker(event, ["startTime", "endTime", "duration", "rating", "flag"], list_items=["filter", "flag"])
                    progdict = xmldictmaker(event['program'], ["title", "sub-title", "releaseYear", "episodeTitle", "shortDesc", "season", "episode", "id"])

                    timestamp = self.zap2it_timestamps(eventdict['startTime'], eventdict['endTime'])

                    clean_prog_dict = {
                                    "time_start": timestamp['time_start'],
                                    "time_end": timestamp['time_end'],
                                    "duration_minutes": eventdict['duration'],
                                    "thumbnail": "https://zap2it.tmsimg.com/assets/%s.jpg" % eventdict['thumbnail'],
                                    "title": progdict['title'] or "Unavailable",
                                    "sub-title": progdict['sub-title'] or "Unavailable",
                                    "description": progdict['shortDesc'] or "Unavailable",
                                    "rating": eventdict['rating'] or "N/A",
                                    "episodetitle": progdict['episodeTitle'],
                                    "releaseyear": progdict['releaseYear'],
                                    "genres": [],
                                    "seasonnumber": progdict['season'],
                                    "episodenumber": progdict['episode'],
                                    "isnew": False,
                                    "id": str(progdict['id'] or "%s_%s" % (cdict["channelId"], timestamp['time_start'])),
                                    }

                    for f in eventdict['filter']:
                        clean_prog_dict["genres"].append(f.replace('filter-', ''))

                    if 'movie' in clean_prog_dict['genres'] and clean_prog_dict['releaseyear']:
                        clean_prog_dict["sub-title"] = 'Movie: %s' % clean_prog_dict['releaseyear']
                    elif clean_prog_dict['episodetitle']:
                        clean_prog_dict["sub-title"] = clean_prog_dict['episodetitle']

                    if 'New' in eventdict['flag'] and 'live' not in eventdict['flag']:
                        clean_prog_dict["isnew"] = True

                    if not any((d['time_start'] == clean_prog_dict['time_start'] and d['id'] == clean_prog_dict['id']) for d in programguide[str(cdict["channelNo"])]["listing"]):
                        programguide[str(cdict["channelNo"])]["listing"].append(clean_prog_dict)

        return programguide

    def zap2it_timestamps(self, starttime, endtime):
        timestamp = {}
        for time_item, time_value in zip(["time_start", "time_end"], [starttime, endtime]):
            timestamp[time_item] = datetime.datetime.fromisoformat(time_value.replace('Z', '+00:00')).timestamp()
        return timestamp

    def get_cached(self, i_times):

        # Fetch data in `zap_timespan` chunks.
        for i_time in i_times:

            parameters = {
                'aid': self.plugin_utils.config.dict["zap2it"]['affiliate_id'],
                'country': self.plugin_utils.config.dict["zap2it"]['country'],
                'device': self.plugin_utils.config.dict["zap2it"]['device'],
                'headendId': self.plugin_utils.config.dict["zap2it"]['headendid'],
                'isoverride': "true",
                'languagecode': self.plugin_utils.config.dict["zap2it"]['languagecode'],
                'pref': 'm,p',
                'timespan': self.plugin_utils.config.dict["zap2it"]['timespan'],
                'timezone': self.plugin_utils.config.dict["zap2it"]['timezone'],
                'userId': self.plugin_utils.config.dict["zap2it"]['userid'],
                'postalCode': str(self.postalcode),
                'lineupId': '%s-%s-DEFAULT' % (self.plugin_utils.config.dict["zap2it"]['country'], self.plugin_utils.config.dict["zap2it"]['device']),
                'time': i_time,
                'Activity_ID': 1,
                'FromPage': "TV%20Guide",
                }

            url = 'https://tvlistings.zap2it.com/api/grid?'
            url += urllib.parse.urlencode(parameters)
            self.get_cached_item(str(i_time), url)
        cache_list = self.plugin_utils.db.get_plugin_value("cache_list", "epg_cache", "zap2it") or []
        return [self.plugin_utils.db.get_plugin_value(x, "epg_cache", "zap2it") for x in cache_list]

    def get_cached_item(self, cache_key, url):
        cacheitem = self.plugin_utils.db.get_plugin_value(cache_key, "epg_cache", "zap2it")
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

            self.plugin_utils.db.set_plugin_value(cache_key, "epg_cache", result, "zap2it")
            cache_list = self.plugin_utils.db.get_plugin_value("cache_list", "epg_cache", "zap2it") or []
            cache_list.append(cache_key)
            self.plugin_utils.db.set_plugin_value("cache_list", "epg_cache", cache_list, "zap2it")

    def remove_stale_cache(self, zap_time):

        cache_list = self.plugin_utils.db.get_plugin_value("cache_list", "epg_cache", "zap2it") or []
        cache_to_kill = []
        for cacheitem in cache_list:
            cachedate = int(cacheitem)
            if cachedate < zap_time:
                cache_to_kill.append(cacheitem)
                self.plugin_utils.db.delete_plugin_value(cacheitem, "epg_cache", "zap2it")
                self.plugin_utils.logger.info("Removing stale cache:  %s" % cacheitem)
        self.plugin_utils.db.set_plugin_value("cache_list", "epg_cache", [x for x in cache_list if x not in cache_to_kill], "zap2it")

    def clear_cache(self):
        cache_list = self.plugin_utils.db.get_plugin_value("cache_list", "epg_cache", "zap2it") or []
        for cacheitem in cache_list:
            self.plugin_utils.db.delete_plugin_value(cacheitem, "epg_cache", "zap2it")
            self.plugin_utils.logger.info("Removing cache:  %s" % cacheitem)
        self.plugin_utils.db.delete_plugin_value("cache_list", "epg_cache", "zap2it")
