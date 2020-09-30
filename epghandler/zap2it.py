import os
import json
import time
import datetime
import urllib.error
import urllib.parse
import urllib.request


def xmltimestamp_zap(inputtime):
    xmltime = inputtime.replace('Z', '+00:00')
    xmltime = datetime.datetime.fromisoformat(xmltime)
    xmltime = xmltime.strftime('%Y%m%d%H%M%S %z')
    return xmltime


def xmldictmaker(inputdict, req_items, list_items=[], str_items=[]):
    xml_dict = {}

    for origitem in list(inputdict.keys()):
        xml_dict[origitem] = inputdict[origitem]

    for req_item in req_items:
        if req_item not in list(inputdict.keys()):
            xml_dict[req_item] = None
        if not xml_dict[req_item]:
            if req_item in list_items:
                xml_dict[req_item] = []
            elif req_item in str_items:
                xml_dict[req_item] = ""

    return xml_dict


class ZapEPG():

    def __init__(self, config):

        self.config = config.config

        self.postalcode = None

        self.epg_cache = None
        self.cache_dir = config.config["main"]["zap_web_cache"]
        self.epg_cache_file = config.config["zap2xml"]["epg_cache"]
        self.epg_cache = self.epg_cache_open()

    def get_location(self):
        self.postalcode = self.config["zap2xml"]["postalcode"]
        if self.postalcode:
            url = 'http://ipinfo.io/json'
            response = urllib.request.urlopen(url)
            data = json.load(response)
            return data["postal"]

    def epg_cache_open(self):
        epg_cache = None
        if os.path.isfile(self.epg_cache_file):
            with open(self.epg_cache_file, 'r') as epgfile:
                epg_cache = json.load(epgfile)
        return epg_cache

    def get_cached(self, cache_key, delay, url):
        cache_path = self.cache_dir.joinpath(cache_key)
        if cache_path.is_file():
            print('FROM CACHE:', str(cache_path))
            with open(cache_path, 'rb') as f:
                return f.read()
        else:
            print('Fetching:  ', url)
            try:
                resp = urllib.request.urlopen(url)
                result = resp.read()
            except urllib.error.HTTPError as e:
                if e.code == 400:
                    print('Got a 400 error!  Ignoring it.')
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
        for p in self.cache_dir.glob('*'):
            try:
                cachedate = datetime.datetime.strptime(str(p.name), "%Y-%m-%d")
                todaysdate = datetime.datetime.strptime(str(todaydate), "%Y-%m-%d")
                if cachedate >= todaysdate:
                    continue
            except Exception as e:
                print(e)
                pass
            print('Removing stale cache file:', p.name)
            p.unlink()

    def update_epg(self):
        print('Updating Zap2it EPG cache file.')
        programguide = {}

        self.get_location()

        # Start time parameter is now rounded down to nearest `zap_timespan`, in s.
        zap_time = time.mktime(time.localtime())
        zap_time_window = int(self.config["zap2xml"]["timespan"]) * 3600
        zap_time = int(zap_time - (zap_time % zap_time_window))

        # Fetch data in `zap_timespan` chunks.
        for i in range(int(7 * 24 / int(self.config["zap2xml"]["timespan"]))):
            i_time = zap_time + (i * zap_time_window)

            parameters = {
                'aid': self.config["zap2xml"]['affiliate_id'],
                'country': self.config["zap2xml"]['country'],
                'device': self.config["zap2xml"]['device'],
                'headendId': self.config["zap2xml"]['headendid'],
                'isoverride': "true",
                'languagecode': self.config["zap2xml"]['languagecode'],
                'pref': 'm,p',
                'timespan': self.config["zap2xml"]['timespan'],
                'timezone': self.config["zap2xml"]['timezone'],
                'userId': self.config["zap2xml"]['userid'],
                'postalCode': self.postalcode,
                'lineupId': '%s-%s-DEFAULT' % (self.config["zap2xml"]['country'], self.config["zap2xml"]['device']),
                'time': i_time,
                'Activity_ID': 1,
                'FromPage': "TV%20Guide",
                }

            url = 'https://tvlistings.zap2it.com/api/grid?'
            url += urllib.parse.urlencode(parameters)

            result = self.get_cached(str(i_time), self.config["zap2xml"]['delay'], url)
            d = json.loads(result)

            for c in d['channels']:

                cdict = xmldictmaker(c, ["callSign", "name", "channelNo", "channelId", "thumbnail"])

                if str(cdict['channelNo']) not in list(programguide.keys()):

                    programguide[str(cdict['channelNo'])] = {
                                                        "callsign": cdict["callSign"],
                                                        "name": cdict["name"] or cdict["callSign"],  # TODO
                                                        "number": cdict["channelNo"],
                                                        "id": cdict["channelId"],
                                                        "thumbnail": str(cdict['thumbnail']).replace("//", "https://").split("?")[0],
                                                        "listing": [],
                                                        }

                for event in c['events']:

                    eventdict = xmldictmaker(event, ["startTime", "endTime", "duration", "rating", "flag"], list_items=["filter", "flag"])
                    progdict = xmldictmaker(event['program'], ["title", "sub-title", "releaseYear", "episodeTitle", "shortDesc", "season", "episode", "id"])

                    clean_prog_dict = {
                                    "time_start": xmltimestamp_zap(eventdict['startTime']),
                                    "time_end": xmltimestamp_zap(eventdict['endTime']),
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
                                    "id": progdict['id'] or xmltimestamp_zap(eventdict['startTime']),
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

        self.epg_cache = programguide
        with open(self.epg_cache_file, 'w') as epgfile:
            epgfile.write(json.dumps(programguide, indent=4))
        print('Wrote updated Zap2it EPG cache file.')
        return programguide
