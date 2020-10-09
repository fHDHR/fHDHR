import json
import time
import datetime
import urllib.parse

from fHDHR.tools import xmldictmaker, WebReq
from fHDHR.fHDHRerrors import EPGSetupError


class ZapEPG():

    def __init__(self, settings, origserv):
        self.config = settings
        self.origserv = origserv
        self.web = WebReq()

        self.postalcode = self.config.dict["zap2it"]["postalcode"]

        self.web_cache_dir = self.config.dict["filedir"]["epg_cache"]["zap2it"]["web_cache"]

    def get_location(self):
        print("Zap2it postalcode not set, attempting to retrieve.")
        if not self.postalcode:
            try:
                postalcode_url = 'http://ipinfo.io/json'
                postalcode_req = self.web.session.get(postalcode_url)
                data = postalcode_req.json()
                self.postalcode = data["postal"]
            except Exception as e:
                raise EPGSetupError("Unable to automatically optain zap2it postalcode: " + str(e))
        return self.postalcode

    def update_epg(self):
        programguide = {}

        # Start time parameter is now rounded down to nearest `zap_timespan`, in s.
        zap_time = time.mktime(time.localtime())
        zap_time_window = int(self.config.dict["zap2it"]["timespan"]) * 3600
        zap_time = int(zap_time - (zap_time % zap_time_window))

        self.remove_stale_cache(zap_time)

        # Fetch data in `zap_timespan` chunks.
        for i in range(int(7 * 24 / int(self.config.dict["zap2it"]["timespan"]))):
            i_time = zap_time + (i * zap_time_window)

            parameters = {
                'aid': self.config.dict["zap2it"]['affiliate_id'],
                'country': self.config.dict["zap2it"]['country'],
                'device': self.config.dict["zap2it"]['device'],
                'headendId': self.config.dict["zap2it"]['headendid'],
                'isoverride': "true",
                'languagecode': self.config.dict["zap2it"]['languagecode'],
                'pref': 'm,p',
                'timespan': self.config.dict["zap2it"]['timespan'],
                'timezone': self.config.dict["zap2it"]['timezone'],
                'userId': self.config.dict["zap2it"]['userid'],
                'postalCode': str(self.postalcode or self.get_location()),
                'lineupId': '%s-%s-DEFAULT' % (self.config.dict["zap2it"]['country'], self.config.dict["zap2it"]['device']),
                'time': i_time,
                'Activity_ID': 1,
                'FromPage': "TV%20Guide",
                }

            url = 'https://tvlistings.zap2it.com/api/grid?'
            url += urllib.parse.urlencode(parameters)

            result = self.get_cached(str(i_time), self.config.dict["zap2it"]['delay'], url)
            d = json.loads(result)

            for c in d['channels']:

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

                    programguide[str(cdict["channelNo"])]["listing"].append(clean_prog_dict)

        return programguide

    def xmltimestamp_zap(self, inputtime):
        xmltime = inputtime.replace('Z', '+00:00')
        xmltime = datetime.datetime.fromisoformat(xmltime)
        xmltime = xmltime.strftime('%Y%m%d%H%M%S %z')
        return xmltime

    def get_cached(self, cache_key, delay, url):
        cache_path = self.web_cache_dir.joinpath(cache_key)
        if cache_path.is_file():
            print('FROM CACHE:', str(cache_path))
            with open(cache_path, 'rb') as f:
                return f.read()
        else:
            print('Fetching:  ', url)
            resp = self.web.session.get(url)
            result = resp.content
            with open(cache_path, 'wb') as f:
                f.write(result)
            time.sleep(int(delay))
            return result

    def remove_stale_cache(self, zap_time):
        for p in self.web_cache_dir.glob('*'):
            try:
                t = int(p.name)
                if t >= zap_time:
                    continue
            except Exception as e:
                print(e)
                pass
            print('Removing stale cache file:', p.name)
            p.unlink()
