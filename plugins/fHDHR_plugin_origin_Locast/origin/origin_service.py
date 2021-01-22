import datetime
import re
import json

import fHDHR.tools
import fHDHR.exceptions


class OriginService():

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

        self.status_dict = {"donateExp": None}

        self.location = {
                        "latitude": None,
                        "longitude": None,
                        "DMA": None,
                        "city": None,
                        "active": False
                        }
        self.zipcode = self.fhdhr.config.dict["origin"]["override_zipcode"]
        self.mock_location = self.format_mock_location()

        self.login()

    def login(self):
        self.fhdhr.logger.info("Logging into Locast using username %s..." % self.fhdhr.config.dict["origin"]["username"])
        self.token = self.get_token()
        if not self.token:
            raise fHDHR.exceptions.OriginSetupError("Locast Login Failed")
        else:
            self.fhdhr.logger.info("Locast Login Success")
            self.status_dict["Login"] = "Success"
            self.fhdhr.config.write(self.fhdhr.config.dict["main"]["dictpopname"], 'token', self.token)
        return True

    def get_token(self):

        login_url = "https://api.locastnet.org/api/user/login"
        login_headers = {'Content-Type': 'application/json'}

        login_json = ("{"
                      "\"username\":\"%s\","
                      "\"password\":\"%s\""
                      "}"
                      % (self.fhdhr.config.dict["origin"]["username"],
                         self.fhdhr.config.dict["origin"]["password"])
                      ).encode("utf-8")

        try:
            loginReq = self.fhdhr.web.session.post(login_url, data=login_json, headers=login_headers)
            loginReq.raise_for_status()
        except self.fhdhr.web.exceptions.HTTPError as err:
            self.fhdhr.logger.error('Login Failed: %s' % err)
            return None

        try:
            loginRes = loginReq.json()
        except json.JSONDecodeError as err:
            self.fhdhr.logger.error('Login Failed: %s' % err)
            return None
        token = loginRes["token"]

        try:
            user_url = "https://api.locastnet.org/api/user/me"
            user_headers = {
                             'Content-Type': 'application/json',
                             'authorization': 'Bearer %s' % token}
            userReq = self.fhdhr.web.session.get(user_url, headers=user_headers)
            userReq.raise_for_status()
        except self.fhdhr.web.exceptions.HTTPError as err:
            self.fhdhr.logger.error('Login Failed: %s' % err)
            return None

        try:
            userresp = userReq.json()
        except json.JSONDecodeError as err:
            self.fhdhr.logger.error('Login Failed: %s' % err)
            return None
        self.fhdhr.logger.info("User Info obtained.")

        if (userresp['didDonate'] and
           datetime.datetime.now() > datetime.datetime.fromtimestamp(userresp['donationExpire'] / 1000)):
            self.fhdhr.logger.error("Donation expired")
            return False
        elif not userresp['didDonate']:
            self.fhdhr.logger.error("User didn't donate")
            return False
        else:
            donateExp = datetime.datetime.fromtimestamp(userresp['donationExpire'] / 1000)
            self.fhdhr.logger.info("User donationExpire: {}".format(donateExp))
            self.status_dict["donateExp"] = donateExp

        if self.find_location():
            self.fhdhr.logger.info("Got location as {} - DMA {} - Lat\Lon {}\{}"
                                   .format(self.location['city'],
                                           self.location['DMA'],
                                           self.location['latitude'],
                                           self.location['longitude']))
        else:
            return False

        # Check that Locast reports this market is currently active and available.
        if not self.location['active']:
            self.fhdhr.logger.info("Locast reports that this DMA\Market area is not currently active!")
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
            req = self.fhdhr.web.session.get(location_url, headers=location_headers)
            req.raise_for_status()
        except self.fhdhr.web.exceptions.HTTPError:
            self.fhdhr.logger.error("Unable to retrieve %s location." % location_type)
            return False
        try:
            geoRes = req.json()
        except json.JSONDecodeError:
            self.fhdhr.logger.error("Unable to retrieve %s location." % location_type)
            return False
        self.set_location(geoRes)
        return True

    def get_zip_location(self):
        """Get geolocation via Locast, based on user provided zipcode."""
        self.fhdhr.logger.info("Getting location via provided zipcode {}".format(self.zipcode))
        location_url = 'https://api.locastnet.org/api/watch/dma/zip/{}'.format(self.zipcode)
        return self.get_geores_json(location_url, "ZIP")

    def get_ip_location(self):
        """Get geolocation via Locast by IP."""
        self.fhdhr.logger.info("Getting location via IP Address.")
        location_url = 'https://api.locastnet.org/api/watch/dma/ip'
        return self.get_geores_json(location_url, "IP")

    def get_coord_location(self):
        self.fhdhr.logger.info("Getting location via provided lat\lon coordinates.")
        # Get geolocation via Locast, using lat\lon coordinates.
        lat = self.mock_location['latitude']
        lon = self.mock_location['longitude']
        location_url = 'https://api.locastnet.org/api/watch/dma/{}/{}'.format(lat, lon)
        return self.get_geores_json(location_url, "Coordinate")

    def format_mock_location(self):
        if (not self.fhdhr.config.dict["origin"]["override_latitude"] or
           not self.fhdhr.config.dict["origin"]["override_longitude"]):
            return None
        else:
            loc_dict = {
                          "latitude": self.fhdhr.config.dict["origin"]["override_latitude"],
                          "longitude": self.fhdhr.config.dict["origin"]["override_longitude"],
                          }
            return loc_dict
