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


def duration_nextpvr_minutes(starttime, endtime):
    return ((int(endtime) - int(starttime))/1000/60)


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

                if str(c['channelNo']) not in list(programguide.keys()):
                    programguide[str(c['channelNo'])] = {}

                channel_thumb = str(c['thumbnail']).replace("//", "https://").split("?")[0]
                programguide[str(c["channelNo"])]["thumbnail"] = channel_thumb

                if "name" not in list(programguide[str(c["channelNo"])].keys()):
                    programguide[str(c["channelNo"])]["name"] = c["callSign"]

                if "callsign" not in list(programguide[str(c["channelNo"])].keys()):
                    programguide[str(c["channelNo"])]["callsign"] = c["callSign"]

                if "id" not in list(programguide[str(c["channelNo"])].keys()):
                    programguide[str(c["channelNo"])]["id"] = c["channelId"]

                if "number" not in list(programguide[str(c["channelNo"])].keys()):
                    programguide[str(c["channelNo"])]["number"] = c["channelNo"]

                if "listing" not in list(programguide[str(c["channelNo"])].keys()):
                    programguide[str(c["channelNo"])]["listing"] = []

                for event in c['events']:
                    clean_prog_dict = {}

                    prog_in = event['program']

                    clean_prog_dict["time_start"] = xmltimestamp_zap(event['startTime'])
                    clean_prog_dict["time_end"] = xmltimestamp_zap(event['endTime'])
                    clean_prog_dict["duration_minutes"] = event['duration']

                    content_thumb = str("https://zap2it.tmsimg.com/assets/" + str(event['thumbnail']) + ".jpg")
                    clean_prog_dict["thumbnail"] = content_thumb

                    if 'title' not in list(prog_in.keys()):
                        prog_in["title"] = "Unavailable"
                    elif not prog_in["title"]:
                        prog_in["title"] = "Unavailable"
                    clean_prog_dict["title"] = prog_in["title"]

                    clean_prog_dict["genres"] = []
                    if 'filter' in list(event.keys()):
                        for f in event['filter']:
                            clean_prog_dict["genres"].append(f.replace('filter-', ''))

                    if 'filter-movie' in event['filter'] and prog_in['releaseYear']:
                        clean_prog_dict["sub-title"] = 'Movie: ' + prog_in['releaseYear']
                    elif prog_in['episodeTitle']:
                        clean_prog_dict["sub-title"] = prog_in['episodeTitle']
                    else:
                        clean_prog_dict["sub-title"] = "Unavailable"

                    clean_prog_dict['releaseyear'] = prog_in['releaseYear']

                    if prog_in['shortDesc'] is None:
                        prog_in['shortDesc'] = "Unavailable"
                    clean_prog_dict["description"] = prog_in['shortDesc']

                    if 'rating' not in list(event.keys()):
                        event['rating'] = "N/A"
                    clean_prog_dict['rating'] = event['rating']

                    if 'season' in list(prog_in.keys()) and 'episode' in list(prog_in.keys()):
                        clean_prog_dict["seasonnumber"] = prog_in['season']
                        clean_prog_dict["episodenumber"] = prog_in['episode']
                        clean_prog_dict["episodetitle"] = clean_prog_dict["sub-title"]
                    else:
                        if "movie" not in clean_prog_dict["genres"]:
                            clean_prog_dict["episodetitle"] = clean_prog_dict["sub-title"]

                    if 'New' in event['flag'] and 'live' not in event['flag']:
                        clean_prog_dict["isnew"] = True

                    programguide[str(c["channelNo"])]["listing"].append(clean_prog_dict)

        self.epg_cache = programguide
        with open(self.epg_cache_file, 'w') as epgfile:
            epgfile.write(json.dumps(programguide, indent=4))
        print('Wrote updated Zap2it EPG cache file.')
        return programguide
