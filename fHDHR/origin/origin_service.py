import datetime
import json
import urllib.request
import re

import fHDHR.tools
import fHDHR.exceptions


class OriginService():

    def __init__(self, settings, logger, web):
        self.config = settings
        self.logger = logger
        self.web = web

        self.status_dict = {"donateExp": None}

        self.location = {
                        "latitude": None,
                        "longitude": None,
                        "DMA": None,
                        "city": None,
                        "active": False
                        }
        self.zipcode = self.config.dict["origin"]["override_zipcode"]
        self.mock_location = self.format_mock_location()

        self.login()

    def login(self):
        self.logger.info("Logging into Locast using username " + self.config.dict["origin"]["username"] + "...")
        self.token = self.get_token()
        if not self.token:
            raise fHDHR.exceptions.OriginSetupError("Locast Login Failed")
        else:
            self.logger.info("Locast Login Success")
            self.status_dict["Login"] = "Success"
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

        self.logger.info("User Info obtained.")
        self.logger.info("User didDonate: {}".format(userresp['didDonate']))
        # Check if the user has donated, and we got an actual expiration date.
        if userresp['didDonate'] and userresp['donationExpire']:
            # Check if donation has expired.
            donateExp = datetime.datetime.fromtimestamp(userresp['donationExpire'] / 1000)
            self.logger.info("User donationExpire: {}".format(donateExp))
            if datetime.datetime.utcnow() > donateExp:
                self.logger.error("Error!  User's donation ad-free period has expired.")
                return False
            else:
                self.status_dict["donateExp"] = donateExp
        else:
            self.logger.error("Error!  User must donate for this to work.")
            return False

        if self.find_location():
            self.logger.info("Got location as {} - DMA {} - Lat\Lon {}\{}".format(self.location['city'],
                                                                                  self.location['DMA'],
                                                                                  self.location['latitude'],
                                                                                  self.location['longitude'])
                             )
        else:
            return False

        # Check that Locast reports this market is currently active and available.
        if not self.location['active']:
            self.logger.info("Locast reports that this DMA\Market area is not currently active!")
            return False

        return token

    def get_status_dict(self):
        ret_status_dict = {
            "Login": "Success",
            "Username": self.config.dict["origin"]["username"],
            "DMA": self.location["DMA"],
            "City": self.location["city"],
            "Latitude": self.location["latitude"],
            "Longitude": self.location["longitude"],
            "Donation Expiration": fHDHR.tools.humanized_time(int((self.status_dict["donateExp"] - datetime.datetime.utcnow()).total_seconds()))
            }
        return ret_status_dict

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
        self.logger.info("Getting location via provided zipcode {}".format(self.zipcode))
        # Get geolocation via Locast, based on user provided zipcode.
        req = urllib.request.Request('https://api.locastnet.org/api/watch/dma/zip/{}'.format(self.zipcode))
        resp = urllib.request.urlopen(req)
        geoRes = json.load(resp)
        self.set_location(geoRes)
        return True

    def get_ip_location(self):
        self.logger.info("Getting location via IP Address.")
        # Get geolocation via Locast. Mirror their website and use https://ipinfo.io/ip to get external IP.
        ip_resp = urllib.request.urlopen('https://ipinfo.io/ip')
        ip = ip_resp.read().strip()
        ip_resp.close()

        self.logger.info("Got external IP {}.".format(ip.decode('utf-8')))

        # Query Locast by IP, using a 'client_ip' header.
        req = urllib.request.Request('https://api.locastnet.org/api/watch/dma/ip')
        req.add_header('client_ip', ip)
        resp = urllib.request.urlopen(req)
        geoRes = json.load(resp)
        resp.close()
        self.set_location(geoRes)
        return True

    def get_coord_location(self):
        self.logger.info("Getting location via provided lat\lon coordinates.")
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
                          "latitude": self.config.dict["origin"]["override_latitude"],
                          "longitude": self.config.dict["origin"]["override_longitude"],
                          }
            return loc_dict
