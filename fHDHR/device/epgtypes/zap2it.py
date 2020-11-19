import datetime
import urllib.parse

from fHDHR.tools import xmldictmaker
from fHDHR.exceptions import EPGSetupError


class zap2itEPG():

    def __init__(self, fhdhr, channels):
        self.fhdhr = fhdhr

        self.channels = channels

        self.postalcode = self.fhdhr.config.dict["zap2it"]["postalcode"]

    def get_location(self):
        self.fhdhr.logger.warning("Zap2it postalcode not set, attempting to retrieve.")
        if not self.postalcode:
            try:
                postalcode_url = 'http://ipinfo.io/json'
                postalcode_req = self.fhdhr.web.session.get(postalcode_url)
                data = postalcode_req.json()
                self.postalcode = data["postal"]
            except Exception as e:
                raise EPGSetupError("Unable to automatically optain zap2it postalcode: " + str(e))
        return self.postalcode

    def update_epg(self):
        programguide = {}

        # Start time parameter is now rounded down to nearest `zap_timespan`, in s.
        zap_time = datetime.datetime.utcnow().timestamp()
        self.remove_stale_cache(zap_time)
        zap_time_window = int(self.fhdhr.config.dict["zap2it"]["timespan"]) * 3600
        zap_time = int(zap_time - (zap_time % zap_time_window))

        # Fetch data in `zap_timespan` chunks.
        i_times = []
        for i in range(int(7 * 24 / int(self.fhdhr.config.dict["zap2it"]["timespan"]))):
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

                    clean_prog_dict = {
                                    "time_start": self.xmltimestamp_zap(eventdict['startTime']),
                                    "time_end": self.xmltimestamp_zap(eventdict['endTime']),
                                    "duration_minutes": eventdict['duration'],
                                    "thumbnail": str("https://zap2it.tmsimg.com/assets/" + str(eventdict['thumbnail']) + ".jpg"),
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
                                    "id": str(progdict['id'] or self.xmltimestamp_zap(eventdict['startTime'])),
                                    }

                    for f in eventdict['filter']:
                        clean_prog_dict["genres"].append(f.replace('filter-', ''))

                    if 'movie' in clean_prog_dict['genres'] and clean_prog_dict['releaseyear']:
                        clean_prog_dict["sub-title"] = 'Movie: ' + clean_prog_dict['releaseyear']
                    elif clean_prog_dict['episodetitle']:
                        clean_prog_dict["sub-title"] = clean_prog_dict['episodetitle']

                    if 'New' in eventdict['flag'] and 'live' not in eventdict['flag']:
                        clean_prog_dict["isnew"] = True

                    if not any(d['id'] == clean_prog_dict['id'] for d in programguide[str(cdict["channelNo"])]["listing"]):
                        programguide[str(cdict["channelNo"])]["listing"].append(clean_prog_dict)

        return programguide

    def xmltimestamp_zap(self, inputtime):
        xmltime = inputtime.replace('Z', '+00:00')
        xmltime = datetime.datetime.fromisoformat(xmltime)
        xmltime = xmltime.strftime('%Y%m%d%H%M%S %z')
        return xmltime

    def get_cached(self, i_times):

        # Fetch data in `zap_timespan` chunks.
        for i_time in i_times:

            parameters = {
                'aid': self.fhdhr.config.dict["zap2it"]['affiliate_id'],
                'country': self.fhdhr.config.dict["zap2it"]['country'],
                'device': self.fhdhr.config.dict["zap2it"]['device'],
                'headendId': self.fhdhr.config.dict["zap2it"]['headendid'],
                'isoverride': "true",
                'languagecode': self.fhdhr.config.dict["zap2it"]['languagecode'],
                'pref': 'm,p',
                'timespan': self.fhdhr.config.dict["zap2it"]['timespan'],
                'timezone': self.fhdhr.config.dict["zap2it"]['timezone'],
                'userId': self.fhdhr.config.dict["zap2it"]['userid'],
                'postalCode': str(self.postalcode or self.get_location()),
                'lineupId': '%s-%s-DEFAULT' % (self.fhdhr.config.dict["zap2it"]['country'], self.fhdhr.config.dict["zap2it"]['device']),
                'time': i_time,
                'Activity_ID': 1,
                'FromPage': "TV%20Guide",
                }

            url = 'https://tvlistings.zap2it.com/api/grid?'
            url += urllib.parse.urlencode(parameters)
            self.get_cached_item(str(i_time), url)
        cache_list = self.fhdhr.db.get_cacheitem_value("cache_list", "offline_cache", "zap2it") or []
        return [self.fhdhr.db.get_cacheitem_value(x, "offline_cache", "zap2it") for x in cache_list]

    def get_cached_item(self, cache_key, url):
        cacheitem = self.fhdhr.db.get_cacheitem_value(cache_key, "offline_cache", "zap2it")
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

            self.fhdhr.db.set_cacheitem_value(cache_key, "offline_cache", result, "zap2it")
            cache_list = self.fhdhr.db.get_cacheitem_value("cache_list", "offline_cache", "zap2it") or []
            cache_list.append(cache_key)
            self.fhdhr.db.set_cacheitem_value("cache_list", "offline_cache", cache_list, "zap2it")

    def remove_stale_cache(self, zap_time):

        cache_list = self.fhdhr.db.get_cacheitem_value("cache_list", "offline_cache", "zap2it") or []
        cache_to_kill = []
        for cacheitem in cache_list:
            cachedate = int(cacheitem)
            if cachedate < zap_time:
                cache_to_kill.append(cacheitem)
                self.fhdhr.db.delete_cacheitem_value(cacheitem, "offline_cache", "zap2it")
                self.fhdhr.logger.info('Removing stale cache:  ' + str(cacheitem))
        self.fhdhr.db.set_cacheitem_value("cache_list", "offline_cache", [x for x in cache_list if x not in cache_to_kill], "zap2it")

    def clear_cache(self):
        cache_list = self.fhdhr.db.get_cacheitem_value("cache_list", "offline_cache", "zap2it") or []
        for cacheitem in cache_list:
            self.fhdhr.db.delete_cacheitem_value(cacheitem, "offline_cache", "zap2it")
            self.fhdhr.logger.info('Removing cache:  ' + str(cacheitem))
        self.fhdhr.db.delete_cacheitem_value("cache_list", "offline_cache", "zap2it")
