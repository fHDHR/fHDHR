import datetime
import re
import json

import fHDHR.tools
from fHDHR.tools import isint, isfloat
import fHDHR.exceptions


class Plugin_OBJ():

    def __init__(self, plugin_utils):
        self.plugin_utils = plugin_utils

        self.status_dict = {"donateExp": None}

        self.location = {
                        "latitude": None,
                        "longitude": None,
                        "DMA": None,
                        "city": None,
                        "active": False
                        }
        self.zipcode = self.plugin_utils.config.dict["locast"]["override_zipcode"]
        self.mock_location = self.format_mock_location()

        self.tuners = self.plugin_utils.config.dict["locast"]["tuners"]

        self.login()

    def get_channels(self):

        stations_url = 'https://api.locastnet.org/api/watch/epg/%s' % self.location["DMA"]
        url_headers = {'Content-Type': 'application/json', 'authorization': 'Bearer %s' % self.token}

        try:
            stationsReq = self.plugin_utils.web.session.get(stations_url, headers=url_headers)
            stationsReq.raise_for_status()
        except self.plugin_utils.web.exceptions.SSLError as err:
            self.plugin_utils.logger.error('Error while getting stations: %s' % err)
            return []
        except self.plugin_utils.web.exceptions.HTTPError as err:
            self.plugin_utils.logger.error('Error while getting stations: %s' % err)
            return []

        stationsRes = stationsReq.json()

        cleaned_channels = []
        for station_item in stationsRes:

            thumbnails = []
            for thumb_opt in ["logo226Url", "logoUrl"]:

                try:
                    thumbnail = station_item[thumb_opt]
                except TypeError:
                    thumbnail = None
                except KeyError:
                    thumbnail = None
                if thumbnail:
                    thumbnails.append(thumbnail)
            if not len(thumbnails):
                thumbnails = [None]

            clean_station_item = {
                                 "name": station_item["name"],
                                 "id": station_item["id"],
                                 "thumbnail": thumbnails[0]
                                 }

            # Typically this will be `2.1 KTTW` but occasionally Locast only provides a channel number here
            # fHDHR device.channels will provide us a number if that is the case
            if (isint(str(station_item['callSign']).split(" ")[0])
               or isfloat(str(station_item['callSign']).split(" ")[0])):
                clean_station_item["number"] = str(station_item['callSign']).split(" ")[0]
                clean_station_item["callsign"] = str(" ".join(station_item['callSign'].split(" ")[1:]))
            else:
                clean_station_item["callsign"] = str(station_item['callSign'])

            cleaned_channels.append(clean_station_item)
        return cleaned_channels

    def get_channel_stream(self, chandict, stream_args):

        videoUrl = "https://api.locastnet.org/api/watch/station/%s/%s/%s" % (chandict["origin_id"], self.location['latitude'], self.location['longitude'])

        videoUrl_headers = {
                            'Content-Type': 'application/json',
                            'authorization': 'Bearer %s' % self.token,
                            'User-Agent': "curl/7.64.1"}

        try:
            videoUrlReq = self.plugin_utils.web.session.get(videoUrl, headers=videoUrl_headers)
            videoUrlReq.raise_for_status()
        except self.plugin_utils.web.exceptions.HTTPError as err:
            self.plugin_utils.logger.error('Error while getting station URL: %s' % err)
            return None

        videoUrlRes = videoUrlReq.json()

        stream_info = {"url": videoUrlRes['streamUrl']}

        return stream_info

    def login(self):
        self.plugin_utils.logger.info("Logging into Locast using username %s..." % self.plugin_utils.config.dict["locast"]["username"])
        self.token = self.get_token()
        if not self.token:
            raise fHDHR.exceptions.OriginSetupError("Locast Login Failed")
        else:
            self.plugin_utils.logger.info("Locast Login Success")
            self.status_dict["Login"] = "Success"
            self.plugin_utils.config.write('token', self.token, "locast")
        return True

    def get_token(self):

        login_url = "https://api.locastnet.org/api/user/login"
        login_headers = {'Content-Type': 'application/json'}

        login_json = ("{"
                      "\"username\":\"%s\","
                      "\"password\":\"%s\""
                      "}"
                      % (self.plugin_utils.config.dict["locast"]["username"],
                         self.plugin_utils.config.dict["locast"]["password"])
                      ).encode("utf-8")

        try:
            loginReq = self.plugin_utils.web.session.post(login_url, data=login_json, headers=login_headers)
            loginReq.raise_for_status()
        except self.plugin_utils.web.exceptions.HTTPError as err:
            self.plugin_utils.logger.error('Login Failed: %s' % err)
            return None

        try:
            loginRes = loginReq.json()
        except json.JSONDecodeError as err:
            self.plugin_utils.logger.error('Login Failed: %s' % err)
            return None
        token = loginRes["token"]

        try:
            user_url = "https://api.locastnet.org/api/user/me"
            user_headers = {
                             'Content-Type': 'application/json',
                             'authorization': 'Bearer %s' % token}
            userReq = self.plugin_utils.web.session.get(user_url, headers=user_headers)
            userReq.raise_for_status()
        except self.plugin_utils.web.exceptions.HTTPError as err:
            self.plugin_utils.logger.error('Login Failed: %s' % err)
            return None

        try:
            userresp = userReq.json()
        except json.JSONDecodeError as err:
            self.plugin_utils.logger.error('Login Failed: %s' % err)
            return None
        self.plugin_utils.logger.info("User Info obtained.")

        if (userresp['didDonate'] and
           datetime.datetime.now() > datetime.datetime.fromtimestamp(userresp['donationExpire'] / 1000)):
            self.plugin_utils.logger.error("Donation expired")
            return False
        elif not userresp['didDonate']:
            self.plugin_utils.logger.error("User didn't donate")
            return False
        else:
            donateExp = datetime.datetime.fromtimestamp(userresp['donationExpire'] / 1000)
            self.plugin_utils.logger.info("User donationExpire: {}".format(donateExp))
            self.status_dict["donateExp"] = donateExp

        if self.find_location():
            self.plugin_utils.logger.info("Got location as {} - DMA {} - Lat\Lon {}\{}"
                                          .format(self.location['city'],
                                                  self.location['DMA'],
                                                  self.location['latitude'],
                                                  self.location['longitude']))
        else:
            return False

        # Check that Locast reports this market is currently active and available.
        if not self.location['active']:
            self.plugin_utils.logger.info("Locast reports that this DMA\Market area is not currently active!")
            return False

        return token

    def set_location(self, geoRes):
        self.location["latitude"] = str(geoRes['latitude'])
        self.location["longitude"] = str(geoRes['longitude'])
        self.location["DMA"] = str(geoRes['DMA'])
        self.location["active"] = geoRes['active']
        self.location["city"] = str(geoRes['name'])

    def find_location(self):
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

    def get_geores_json(self, location_url, location_type):
        location_headers = {'Content-Type': 'application/json'}
        try:
            req = self.plugin_utils.web.session.get(location_url, headers=location_headers)
            req.raise_for_status()
        except self.plugin_utils.web.exceptions.HTTPError:
            self.plugin_utils.logger.error("Unable to retrieve %s location." % location_type)
            return False
        try:
            geoRes = req.json()
        except json.JSONDecodeError:
            self.plugin_utils.logger.error("Unable to retrieve %s location." % location_type)
            return False
        self.set_location(geoRes)
        return True

    def get_zip_location(self):
        """Get geolocation via Locast, based on user provided zipcode."""
        self.plugin_utils.logger.info("Getting location via provided zipcode {}".format(self.zipcode))
        location_url = 'https://api.locastnet.org/api/watch/dma/zip/{}'.format(self.zipcode)
        return self.get_geores_json(location_url, "ZIP")

    def get_ip_location(self):
        """Get geolocation via Locast by IP."""
        self.plugin_utils.logger.info("Getting location via IP Address.")
        location_url = 'https://api.locastnet.org/api/watch/dma/ip'
        return self.get_geores_json(location_url, "IP")

    def get_coord_location(self):
        self.plugin_utils.logger.info("Getting location via provided lat\lon coordinates.")
        # Get geolocation via Locast, using lat\lon coordinates.
        lat = self.mock_location['latitude']
        lon = self.mock_location['longitude']
        location_url = 'https://api.locastnet.org/api/watch/dma/{}/{}'.format(lat, lon)
        return self.get_geores_json(location_url, "Coordinate")

    def format_mock_location(self):
        if (not self.plugin_utils.config.dict["locast"]["override_latitude"] or
           not self.plugin_utils.config.dict["locast"]["override_longitude"]):
            return None
        else:
            loc_dict = {
                          "latitude": self.plugin_utils.config.dict["locast"]["override_latitude"],
                          "longitude": self.plugin_utils.config.dict["locast"]["override_longitude"],
                          }
            return loc_dict
