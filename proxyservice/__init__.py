import os
import json
import datetime
import urllib.error
import urllib.parse
import urllib.request

from . import locastauth
from . import locastlocation


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


class proxyserviceFetcher():

    def __init__(self, config):
        self.config = config.copy()

        self.video_records = {}

        self.epg_cache = None
        self.cache_dir = self.config["main"]["proxy_web_cache"]
        self.epg_cache_file = self.config["proxy"]["epg_cache"]

        self.urls = {}
        self.url_assembler()

        self.auth = locastauth.Locast_Auth(config)
        self.location_info = locastlocation.LocastDMAFinder(config)
        self.location = self.location_info.location

        self.epg_cache = self.epg_cache_open()

    def epg_cache_open(self):
        epg_cache = None
        if os.path.isfile(self.epg_cache_file):
            with open(self.epg_cache_file, 'r') as epgfile:
                epg_cache = json.load(epgfile)
        return epg_cache

    def thumb_url(self, thumb_type, base_url, thumbnail):
        if thumb_type == "channel":
            return thumbnail
        elif thumb_type == "content":
            return thumbnail

    def url_assembler(self):
        pass

    def get_channels(self):
        self.auth.check_token()

        stationsReq = urllib.request.Request('https://api.locastnet.org/api/watch/epg/' +
                                             str(self.location["DMA"]),
                                             headers={'Content-Type': 'application/json',
                                                      'authorization': 'Bearer ' + self.auth.token})

        stationsOpn = urllib.request.urlopen(stationsReq)
        stationsRes = json.load(stationsOpn)
        stationsOpn.close()

        for index, locast_station in enumerate(stationsRes):
            try:
                assert(float(locast_station['callSign'].split()[0]))
                stationsRes[index]['channel'] = locast_station['callSign'].split()[0]
            except ValueError:
                pass

        cleaned_channels = []
        for station_item in stationsRes:
            clean_station_item = {
                                 "name": station_item["name"],
                                 "callsign": str(station_item['callSign']).split(" ")[1],
                                 "number": str(station_item['callSign']).split(" ")[0],
                                 "id": station_item["id"],
                                 }
            cleaned_channels.append(clean_station_item)
        return cleaned_channels

    def get_station_list(self, base_url):
        station_list = []

        for c in self.get_channels():
            if self.config["fakehdhr"]["stream_type"] == "ffmpeg":
                watchtype = "ffmpeg"
            else:
                watchtype = "direct"
            url = ('%s%s/watch?method=%s&channel=%s' %
                   ("http://",
                    base_url,
                    watchtype,
                    c['id']
                    ))
            station_list.append(
                                {
                                 'GuideNumber': str(c['number']),
                                 'GuideName': c['name'],
                                 'URL': url
                                })
        return station_list

    def get_station_total(self):
        total_channels = 0
        for c in self.get_channels():
            total_channels += 1
        return total_channels

    def get_channel_stream(self, station_id):
        print("Getting station info for " + station_id + "...")

        try:
            videoUrlReq = urllib.request.Request('https://api.locastnet.org/api/watch/station/' +
                                                 str(station_id) + '/' +
                                                 self.location['latitude'] + '/' +
                                                 self.location['longitude'],
                                                 headers={'Content-Type': 'application/json',
                                                          'authorization': 'Bearer ' + self.auth.token})
            videoUrlOpn = urllib.request.urlopen(videoUrlReq)
            videoUrlRes = json.load(videoUrlOpn)
            # videoUrlOpn.close()
        except urllib.error.URLError as urlError:
            print("Error when getting the video URL: " + str(urlError.reason))
            return False
        except urllib.error.HTTPError as httpError:
            print("Error when getting the video URL: " + str(httpError.reason))
            return False
        except Exception as e:
            print(e)
            print("Error when getting the video URL: " + str(e))
            return False
        return videoUrlRes['streamUrl']

    def get_channel_streams(self):
        self.auth.check_token()
        streamdict = {}
        for c in self.get_channels():
            videoUrl = ('https://api.locastnet.org/api/watch/station/' +
                        str(c["id"]) + '/' +
                        self.location['latitude'] + '/' +
                        self.location['longitude'])
            videoUrlReq = urllib.request.Request(videoUrl, headers={'Content-Type': 'application/json',
                                                                    'authorization': 'Bearer ' + self.auth.token})
            videoUrlOpn = urllib.request.urlopen(videoUrlReq)
            videoUrlRes = json.load(videoUrlOpn)
            videoUrlOpn.close()
            streamdict[str(c["id"])] = videoUrlRes['streamUrl']
        return streamdict

    def get_channel_thumbnail(self, channel_id):
        channel_thumb_url = "todo"
        return channel_thumb_url

    def get_content_thumbnail(self, content_id):
        self.auth.check_token()
        item_thumb_url = "todo"
        return item_thumb_url

    def update_epg(self):
        print('Updating ' + self.config["main"]["servicename"] + ' EPG cache file.')
        self.auth.check_token()

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
                   str(self.location["DMA"]) + "?startTime=" + str(x_date))

            result = self.get_cached(str(x_date), url)
            d = json.loads(result)

            for c in d:

                cdict = xmldictmaker(c, ["callSign", "name", "channelId"], list_items=[], str_items=[])

                channel_number = str(cdict['callSign']).split(" ")[0]

                if str(channel_number) not in list(programguide.keys()):
                    programguide[str(channel_number)] = {
                                                      "callsign": str(cdict['name']),
                                                      "name": str(cdict['callSign']).split(" ")[1],
                                                      "number": channel_number,
                                                      "id": cdict["id"],
                                                      "thumbnail": str(cdict['logo226Url']),
                                                      "listing": [],
                                                      }

                for event in c['listings']:

                    eventdict = xmldictmaker(event, ["startTime", "endTime", "duration", "preferredImage",
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
                                    "id": eventdict['programId']
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

        self.epg_cache = programguide
        with open(self.epg_cache_file, 'w') as epgfile:
            epgfile.write(json.dumps(programguide, indent=4))
        print('Wrote updated ' + self.config["main"]["servicename"] + ' EPG cache file.')
        return programguide

    def get_location(self):
        pass

    def get_cached(self, cache_key, url):
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

    def locast_xmltime(self, tm):
        tm = datetime.datetime.fromtimestamp(tm/1000.0)
        tm = str(tm.strftime('%Y%m%d%H%M%S')) + " +0000"
        return tm
