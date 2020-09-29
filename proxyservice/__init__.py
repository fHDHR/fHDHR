import os
import json
import datetime
import urllib.error
import urllib.parse
import urllib.request

from . import locastauth
from . import location


def xmltimestamp_nextpvr(epochtime):
    xmltime = datetime.datetime.fromtimestamp(int(epochtime)/1000)
    xmltime = str(xmltime.strftime('%Y%m%d%H%M%S')) + " +0000"
    return xmltime


def duration_nextpvr_minutes(starttime, endtime):
    return ((int(endtime) - int(starttime))/1000/60)


class proxyserviceFetcher():

    def __init__(self, config):
        self.config = config.config

        self.epg_cache = None
        self.cache_dir = config.config["main"]["locast_web_cache"]
        self.epg_cache_file = config.config["locast"]["epg_cache"]

        self.servicename = "LocastProxy"

        self.urls = {}
        self.url_assembler()

        self.auth = locastauth.Locast_Auth(config)
        self.location_info = location.LocastDMAFinder(config)
        self.location = self.location_info.location

        self.epg_cache = self.epg_cache_open()

    def epg_cache_open(self):
        epg_cache = None
        if os.path.isfile(self.epg_cache_file):
            with open(self.epg_cache_file, 'r') as epgfile:
                epg_cache = json.load(epgfile)
        return epg_cache

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
                # result like "WDPN" or "CBS" in the callsign field, or the callsign in the name field
                # then we'll search the callsign in a few different lists to get the station channel
                # note: callsign field usually has the most recent data if it contains an actual callsign
                skip_sub_id = False

                # callsign from "callsign" field
                callsign_result = self.detect_callsign(locast_station['callSign'])

                # callsign from "name" field - usually in "[callsign][TYPE][subchannel]" format
                # example: WABCDT2
                alt_callsign_result = self.detect_callsign(locast_station['name'])

                # then check "name"
                if ('channel' not in stationsRes[index]):
                    pass

                # locast usually adds a number in it's callsign (in either field).  that
                # number is the subchannel
                if (not skip_sub_id) and ('channel' in stationsRes[index]):
                    if callsign_result['verified'] and (callsign_result['subchannel'] is not None):
                        stationsRes[index]['channel'] = stationsRes[index]['channel'] + '.' + callsign_result['subchannel']
                    elif alt_callsign_result['verified'] and (alt_callsign_result['subchannel'] is not None):
                        stationsRes[index]['channel'] = stationsRes[index]['channel'] + '.' + alt_callsign_result['subchannel']
                    else:
                        stationsRes[index]['channel'] = stationsRes[index]['channel'] + '.1'

        cleaned_channels = []
        for station_item in stationsRes:
            clean_station_item = {
                                 "name": station_item["callSign"],
                                 "number": station_item["channel"],
                                 "id": station_item["stationId"],
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
                    c['channel']
                    ))
            station_list.append(
                                {
                                 'GuideNumber': str(c['channel']),
                                 'GuideName': c['name'],
                                 'URL': url
                                })
        return station_list

    def get_station_total(self):
        total_channels = 0
        for c in self.get_channels():
            total_channels += 1
        return total_channels

    def get_channel_streams(self):
        streamdict = {}
        for c in self.get_channels():
            url = ('%s%s:%s/live?channel=%s&client=%s' %
                   ("https://" if self.config["nextpvr"]["ssl"] else "http://",
                    self.config["nextpvr"]["address"],
                    str(self.config["nextpvr"]["port"]),
                    str(c["channel"]),
                    str(c["channel"]),
                    ))
            streamdict[str(c["channel"])] = url
        return streamdict

    def get_channel_thumbnail(self, channel_id):
        channel_thumb_url = ("%s%s:%s/service?method=channel.icon&channel_id=%s" %
                             ("https://" if self.config["nextpvr"]["ssl"] else "http://",
                              self.config["nextpvr"]["address"],
                              str(self.config["nextpvr"]["port"]),
                              str(channel_id)
                              ))
        return channel_thumb_url

    def get_content_thumbnail(self, content_id):
        self.auth.check_token()
        item_thumb_url = ("%s%s:%s/service?method=channel.show.artwork&sid=%s&event_id=%s" %
                          ("https://" if self.config["nextpvr"]["ssl"] else "http://",
                           self.config["nextpvr"]["address"],
                           str(self.config["nextpvr"]["port"]),
                           self.auth.config['sid'],
                           str(content_id)
                           ))
        return item_thumb_url

    def update_epg(self):
        print('Updating NextPVR EPG cache file.')
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
            channel_info = json.loads(result)

            for channel_item in channel_info:

                channel_number = str(channel_item['callSign']).split(" ")[0]
                channel_realname = str(channel_item['callSign']).split(" ")[1]
                channel_callsign = str(channel_item['name'])
                channel_ID = str(channel_item['stationId'])
                channel_logo = str(channel_item['logo226Url'])

                if str(channel_number) not in list(programguide.keys()):
                    programguide[str(channel_number)] = {}

                programguide[str(channel_number)]["thumbnail"] = channel_logo

                if "name" not in list(programguide[str(channel_number)].keys()):
                    programguide[str(channel_number)]["name"] = channel_realname

                if "callsign" not in list(programguide[str(channel_number)].keys()):
                    programguide[str(channel_number)]["callsign"] = channel_callsign

                if "id" not in list(programguide[str(channel_number)].keys()):
                    programguide[str(channel_number)]["id"] = channel_ID

                if "number" not in list(programguide[str(channel_number)].keys()):
                    programguide[str(channel_number)]["number"] = channel_number

                if "listing" not in list(programguide[str(channel_number)].keys()):
                    programguide[str(channel_number)]["listing"] = []

            for event in channel_item['listings']:

                clean_prog_dict = {}

                event_genres = []
                if 'genres' in event.keys():
                    event_genres = event['genres'].split(",")
                clean_prog_dict["genres"] = event_genres

                clean_prog_dict["time_start"] = self.locast_xmltime(event['startTime'])
                clean_prog_dict["time_end"] = self.locast_xmltime(event['startTime'] + event['duration'] * 1000)
                clean_prog_dict["duration_minutes"] = event['duration'] * 1000

                if event["preferredImage"] is not None:
                    clean_prog_dict["thumbnail"] = event["preferredImage"]

                if 'title' not in list(event.keys()):
                    event["title"] = "Unavailable"
                elif not event["title"]:
                    event["title"] = "Unavailable"
                clean_prog_dict["title"] = event["title"]

                if 'subtitle' not in list(event.keys()):
                    event["subtitle"] = "Unavailable"
                clean_prog_dict["sub-title"] = event["subtitle"]

                if event['subtitle'].startswith("Movie:"):
                    clean_prog_dict['releaseyear'] = event['subtitle'].split("Movie:")[-1]
                else:
                    clean_prog_dict['releaseyear'] = None

                if 'description' not in list(event.keys()):
                    event["description"] = "Unavailable"
                elif event['description']:
                    event["description"] = "Unavailable"
                clean_prog_dict["description"] = event["description"]

                if 'rating' not in list(event.keys()):
                    event['rating'] = "N/A"
                clean_prog_dict['rating'] = event['rating']

                if 'season' in list(event.keys()) and 'episode' in list(event.keys()):
                    clean_prog_dict["seasonnumber"] = event['season']
                    clean_prog_dict["episodenumber"] = event['episode']
                    clean_prog_dict["episodetitle"] = clean_prog_dict["sub-title"]
                else:
                    if "movie" not in clean_prog_dict["genres"]:
                        clean_prog_dict["episodetitle"] = clean_prog_dict["sub-title"]

                # TODO isNEW

                programguide[str(channel_number)]["listing"].append(clean_prog_dict)

        self.epg_cache = programguide
        with open(self.epg_cache_file, 'w') as epgfile:
            epgfile.write(json.dumps(programguide, indent=4))
        print('Wrote updated NextPVR EPG cache file.')
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
