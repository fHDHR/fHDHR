import json
import datetime
import re
import m3u8

import urllib.request

import fHDHR.tools


class fHDHRservice():
    def __init__(self, settings):
        self.config = settings

        self.web = fHDHR.tools.WebReq()
        self.location = {
                        "latitude": None,
                        "longitude": None,
                        "DMA": None,
                        "city": None,
                        "active": False
                        }
        self.zipcode = self.config.dict["origin"]["override_zipcode"]
        self.mock_location = self.format_mock_location()
        self.web_cache_dir = self.config.dict["filedir"]["epg_cache"]["origin"]["web_cache"]

    def login(self):
        print("Logging into Locast using username " + self.config.dict["origin"]["username"] + "...")
        self.token = self.get_token()
        if not self.token:
            return False
        else:
            print("Locast Login Success")
            self.config.write(self.config.dict["main"]["dictpopname"], 'token', self.token)
        return True

    def get_token(self):
        loginReq = urllib.request.Request('https://api.locastnet.org/api/user/login',
                                          ('{"username":"' + self.config.dict["origin"]["username"] +
                                              '","password":"' + self.config.dict["origin"]["password"] +
                                              '"}').encode("utf-8"),
                                          {'Content-Type': 'application/json'})

        loginOpn = urllib.request.urlopen(loginReq)
        loginRes = json.load(loginOpn)
        loginOpn.close()
        token = loginRes["token"]

        userReq = urllib.request.Request('https://api.locastnet.org/api/user/me',
                                         headers={'Content-Type': 'application/json',
                                                  'authorization': 'Bearer ' + token})

        userOpn = urllib.request.urlopen(userReq)
        userresp = json.load(userOpn)
        userOpn.close()

        print("User Info obtained.")
        print("User didDonate: {}".format(userresp['didDonate']))
        # Check if the user has donated, and we got an actual expiration date.
        if userresp['didDonate'] and userresp['donationExpire']:
            # Check if donation has expired.
            donateExp = datetime.datetime.fromtimestamp(userresp['donationExpire'] / 1000)
            print("User donationExpire: {}".format(donateExp))
            if datetime.datetime.now() > donateExp:
                print("Error!  User's donation ad-free period has expired.")
                return False
        else:
            print("Error!  User must donate for this to work.")
            return False

        if self.find_location():
            print("Got location as {} - DMA {} - Lat\Lon {}\{}".format(self.location['city'],
                                                                       self.location['DMA'],
                                                                       self.location['latitude'],
                                                                       self.location['longitude'])
                  )
        else:
            return False

        # Check that Locast reports this market is currently active and available.
        if not self.location['active']:
            print("Locast reports that this DMA\Market area is not currently active!")
            return False

        return token

    def get_channels(self):

        stationsReq = urllib.request.Request('https://api.locastnet.org/api/watch/epg/' +
                                             str(self.location["DMA"]),
                                             headers={'Content-Type': 'application/json',
                                                      'authorization': 'Bearer ' + self.token})

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

    def get_channel_stream(self, chandict, allchandict):
        caching = True
        streamlist = []
        streamdict = {}
        videoUrlReq = urllib.request.Request('https://api.locastnet.org/api/watch/station/' +
                                             str(chandict["id"]) + '/' +
                                             self.location['latitude'] + '/' +
                                             self.location['longitude'],
                                             headers={'Content-Type': 'application/json',
                                                      'authorization': 'Bearer ' + self.token})
        videoUrlOpn = urllib.request.urlopen(videoUrlReq)
        videoUrlRes = json.load(videoUrlOpn)
        if self.config.dict["origin"]["force_best"]:
            streamurl = self.m3u8_beststream(videoUrlRes['streamUrl'])
        else:
            streamurl = videoUrlRes['streamUrl']
        streamdict = {"number": chandict["number"], "stream_url": streamurl}
        streamlist.append(streamdict)

        return streamlist, caching

    def m3u8_beststream(self, m3u8_url):
        bestStream = None
        videoUrlM3u = m3u8.load(m3u8_url)
        if not videoUrlM3u.is_variant:
            return m3u8_url
        print(videoUrlM3u.playlists)

        for videoStream in videoUrlM3u.playlists:
            if not bestStream:
                bestStream = videoStream
            elif videoStream.stream_info.bandwidth > bestStream.stream_info.bandwidth:
                bestStream = videoStream

        if not bestStream:
            return bestStream.absolute_uri
        else:
            return m3u8_url

    def update_epg(self):
        programguide = {}

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

                cdict = fHDHR.tools.xmldictmaker(c, ["callSign", "name", "channelId"], list_items=[], str_items=[])

                channel_number = str(cdict['callSign']).split(" ")[0]

                if str(channel_number) not in list(programguide.keys()):
                    programguide[str(channel_number)] = {
                                                      "callsign": str(cdict['name']),
                                                      "name": str(cdict['callSign']).split(" ")[1],
                                                      "number": channel_number,
                                                      "id": str(cdict["id"]),
                                                      "thumbnail": str(cdict['logo226Url']),
                                                      "listing": [],
                                                      }

                for event in c['listings']:

                    eventdict = fHDHR.tools.xmldictmaker(event, ["startTime", "endTime", "duration", "preferredImage",
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
                                    "id": str(eventdict['programId'])
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

        return programguide

    def locast_xmltime(self, tm):
        tm = datetime.datetime.fromtimestamp(tm/1000.0)
        tm = str(tm.strftime('%Y%m%d%H%M%S')) + " +0000"
        return tm

    def get_cached(self, cache_key, url):
        cache_path = self.web_cache_dir.joinpath(cache_key)
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
        for p in self.web_cache_dir.glob('*'):
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

    def set_location(self, geoRes):
        self.location["latitude"] = str(geoRes['latitude'])
        self.location["longitude"] = str(geoRes['longitude'])
        self.location["DMA"] = str(geoRes['DMA'])
        self.location["active"] = geoRes['active']
        self.location["city"] = str(geoRes['name'])

    def find_location(self):
        '''
        Mirror the geolocation options found at locast.org/dma since we can't
        rely on browser geolocation. If the user provides override coords, or
        override_zipcode, resolve location based on that data. Otherwise check
        by external ip, (using ipinfo.io, as the site does).
        Calls to Locast return JSON in the following format:
        {
            u'DMA': str (DMA Number),
            u'large_url': str,
            u'name': str,
            u'longitude': lon,
            u'latitude': lat,
            u'active': bool,
            u'announcements': list,
            u'small_url': str
        }
        '''
        zip_format = re.compile(r'^[0-9]{5}$')
        # Check if the user provided override coords.
        if self.mock_location:
            return self.get_coord_location()
        # Check if the user provided an override zipcode, and that it's valid.
        elif self.zipcode and zip_format.match(self.zipcode):
            return self.get_zip_location()
        else:
            # If no override zip, or not a valid ZIP, fallback to IP location.
            return self.get_ip_location()

    def get_zip_location(self):
        print("Getting location via provided zipcode {}".format(self.zipcode))
        # Get geolocation via Locast, based on user provided zipcode.
        req = urllib.request.Request('https://api.locastnet.org/api/watch/dma/zip/{}'.format(self.zipcode))
        resp = urllib.request.urlopen(req)
        geoRes = json.load(resp)
        self.set_location(geoRes)
        return True

    def get_ip_location(self):
        print("Getting location via IP Address.")
        # Get geolocation via Locast. Mirror their website and use https://ipinfo.io/ip to get external IP.
        ip_resp = urllib.request.urlopen('https://ipinfo.io/ip')
        ip = ip_resp.read().strip()
        ip_resp.close()

        print("Got external IP {}.".format(ip.decode('utf-8')))

        # Query Locast by IP, using a 'client_ip' header.
        req = urllib.request.Request('https://api.locastnet.org/api/watch/dma/ip')
        req.add_header('client_ip', ip)
        resp = urllib.request.urlopen(req)
        geoRes = json.load(resp)
        resp.close()
        self.set_location(geoRes)
        return True

    def get_coord_location(self):
        print("Getting location via provided lat\lon coordinates.")
        # Get geolocation via Locast, using lat\lon coordinates.
        lat = self.mock_location['latitude']
        lon = self.mock_location['longitude']
        req = urllib.request.Request('https://api.locastnet.org/api/watch/dma/{}/{}'.format(lat, lon))
        req.add_header('Content-Type', 'application/json')
        resp = urllib.request.urlopen(req)
        geoRes = json.load(resp)
        self.set_location(geoRes)
        return True

    def format_mock_location(self):
        if not self.config.dict["origin"]["override_latitude"] or not self.config.dict["origin"]["override_longitude"]:
            return None
        else:
            loc_dict = {
                          "lat": self.config.dict["origin"]["override_latitude"],
                          "lon": self.config.dict["origin"]["override_longitude"],
                          }
            return loc_dict
