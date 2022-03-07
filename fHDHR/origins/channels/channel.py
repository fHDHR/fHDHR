import time


class Channel():
    """
    fHDHR Channel Object.
    """

    def __init__(self, fhdhr, id_system, origin_obj, origin_id=None, channel_id=None):
        self.fhdhr = fhdhr
        self.id_system = id_system
        self.origin_obj = origin_obj
        self.origin_name = origin_obj.name

        if not channel_id:

            if origin_id:
                channel_id = id_system.get(origin_id, self.origin_obj)

            else:
                channel_id = id_system.assign(self.origin_obj)

        self.channel_id = channel_id

        self.dict = self.fhdhr.db.get_fhdhr_value(str(channel_id), "dict", self.origin_name) or self.default_dict
        self.verify_dict()

        self.save_channel()

    @property
    def number(self):
        """
        Combine Number and subnumber into a string.
        """

        if self.dict["subnumber"]:
            return "%s.%s" % (self.dict["number"], self.dict["subnumber"])
        else:
            return self.dict["number"]

    @property
    def thumbnail(self):
        """
        Get a channel thumbnail.
        """

        if str(self.dict["thumbnail"]).lower() in ["none"]:
            return self.generic_image_url

        elif self.dict["thumbnail"]:
            return self.dict["thumbnail"]

        elif self.dict["origin_thumbnail"]:
            return self.dict["origin_thumbnail"]

        else:
            return self.generic_image_url

    @property
    def epgdict(self):
        """
        Produce dict of channel information.
        """

        return {
                "callsign": self.dict["callsign"],
                "name": self.dict["name"],
                "number": self.number,
                "id": self.dict["origin_id"],
                "thumbnail": self.thumbnail,
                "listing": [],
                }

    def verify_dict(self):
        """
        Development Purposes.
        Add new Channel dict keys.
        """

        default_dict = self.default_dict
        for key in list(default_dict.keys()):

            if key not in list(self.dict.keys()):
                self.dict[key] = default_dict[key]

        if self.dict["number"]:

            if "." in self.dict["number"]:
                self.dict["subnumber"] = self.dict["number"].split(".")[1]
                self.dict["number"] = self.dict["number"].split(".")[0]

        self.dict["favorite"] = int(self.dict["favorite"])

        self.dict["HD"] = int(self.dict["HD"])

        if str(self.dict["enabled"]).lower() in ["true"]:
            self.dict["enabled"] = True
        else:
            self.dict["enabled"] = False

    def basics(self, channel_info):
        """
        Some Channel Information is Critical.
        """

        if "name" not in list(channel_info.keys()):
            channel_info["name"] = self.dict["id"]

        elif not channel_info["name"]:
            channel_info["name"] = self.dict["id"]

        self.dict["origin_name"] = channel_info["name"]
        if not self.dict["name"]:
            self.dict["name"] = self.dict["origin_name"]

        if "id" not in list(channel_info.keys()):
            channel_info["id"] = channel_info["name"]

        elif not channel_info["id"]:
            channel_info["id"] = channel_info["name"]

        self.dict["origin_id"] = channel_info["id"]

        if "callsign" not in list(channel_info.keys()):
            channel_info["callsign"] = channel_info["name"]

        elif not channel_info["callsign"]:
            channel_info["callsign"] = channel_info["name"]

        self.dict["origin_callsign"] = channel_info["callsign"]
        if not self.dict["callsign"]:
            self.dict["callsign"] = self.dict["origin_callsign"]

        if "tags" not in list(channel_info.keys()):
            channel_info["tags"] = []

        elif not channel_info["tags"]:
            channel_info["tags"] = []

        self.dict["origin_tags"] = channel_info["tags"]
        if not self.dict["tags"]:
            self.dict["tags"] = self.dict["origin_tags"]

        if "number" not in list(channel_info.keys()):
            channel_info["number"] = self.id_system.get_number(channel_info["id"], self.origin_obj)

        elif not channel_info["number"]:
            channel_info["number"] = self.id_system.get_number(channel_info["id"], self.origin_obj)

        self.dict["origin_number"] = str(channel_info["number"])
        if not self.dict["number"]:

            self.dict["number"] = self.dict["origin_number"].split(".")[0]
            try:
                self.dict["subnumber"] = self.dict["origin_number"].split(".")[1]
            except IndexError:
                self.dict["subnumber"] = None

        else:

            if "." in self.dict["number"]:
                self.dict["subnumber"] = self.dict["number"].split(".")[1]
                self.dict["number"] = self.dict["number"].split(".")[0]

        if "thumbnail" not in list(channel_info.keys()):
            channel_info["thumbnail"] = None

        self.dict["origin_thumbnail"] = channel_info["thumbnail"]
        if not self.dict["thumbnail"]:
            self.dict["thumbnail"] = self.dict["origin_thumbnail"]

        if "HD" not in list(channel_info.keys()):
            channel_info["HD"] = 0
        self.dict["HD"] = channel_info["HD"]

        if "enabled" in list(channel_info.keys()):

            if "created" not in list(self.dict.keys()):
                self.dict["enabled"] = channel_info["enabled"]

        if "created" not in list(self.dict.keys()):
            self.dict["created"] = time.time()

        self.save_channel()

    @property
    def default_dict(self):
        """
        A default for how a channel listing should appear.
        """

        return {
                "id": str(self.channel_id), "origin_id": None,
                "name": None, "origin_name": None,
                "callsign": None, "origin_callsign": None,
                "number": None, "subnumber": None, "origin_number": None,
                "tags": [], "origin_tags": [],
                "thumbnail": None, "origin_thumbnail": None,
                "enabled": True, "favorite": 0,
                "HD": 0,
                }

    def set_status(self, updatedict):
        """
        Set status of a channel value.
        """

        self.fhdhr.logger.debug("Updating %s channel %s." % (self.origin_name, self.dict["id"]))
        for key in list(updatedict.keys()):

            if key == "number":

                number = updatedict[key]
                if "." in str(number):
                    self.dict["subnumber"] = str(number).split(".")[1]
                    self.dict["number"] = str(number).split(".")[0]

                else:
                    self.dict["number"] = str(number)
                    self.dict["subnumber"] = None

            elif key in ["favorite", "HD"]:
                self.dict[key] = int(updatedict[key])

            elif key in ["enabled"]:
                if str(updatedict[key]).lower() in ["true"]:
                    updatedict[key] = True
                else:
                    updatedict[key] = False
                self.dict[key] = updatedict[key]

            else:
                self.dict[key] = str(updatedict[key])

        self.save_channel()

    @property
    def generic_image_url(self):
        """
        A Generated image url for the channel.
        """

        return "/api/images?method=generate&type=channel&message=%s" % self.number

    @property
    def api_stream_url(self):
        """
        The Url of fHDHR stream for the channel.
        """

        return '/api/tuners?method=stream&channel=%s&origin=%s' % (self.dict["id"], self.origin_name)

    @property
    def api_m3u_url(self):
        """
        The Url of m3u for the channel.
        """

        return '/api/m3u?method=get&channel=%s&origin=%s' % (self.dict["id"], self.origin_name)

    @property
    def api_w3u_url(self):
        """
        The Url of w3u for the channel.
        """

        return '/api/w3u?method=get&channel=%s&origin=%s' % (self.dict["id"], self.origin_name)

    def set_favorite(self, enablement):
        """
        Set Channel Favorite Status.
        """

        self.fhdhr.logger.debug("Setting %s channel %s Facorite status to %s." % (self.origin_name, self.dict["id"], enablement))

        if enablement == "+":
            self.dict["favorite"] = 1

        elif enablement == "-":
            self.dict["favorite"] = 0

        self.save_channel()

    def set_enablement(self, enablement):
        """
        Set Channel Enablement Status.
        """

        self.fhdhr.logger.debug("Setting %s channel %s Enabled status to %s." % (self.origin_name, self.dict["id"], enablement))

        if enablement == "disable":
            self.dict["enabled"] = False

        elif enablement == "enable":
            self.dict["enabled"] = True

        elif enablement == "toggle":

            if self.dict["enabled"]:
                self.dict["enabled"] = False

            else:
                self.dict["enabled"] = True

        self.save_channel()

    def save_channel(self):
        self.fhdhr.db.set_fhdhr_value(self.dict["id"], "dict", self.dict, self.origin_name)

    def delete_channel(self):
        self.fhdhr.db.delete_fhdhr_value(self.dict["id"], "dict", self.origin_name)

    def __getattr__(self, name):
        """
        Quick and dirty shortcuts. Will only get called for undefined attributes.
        """

        if name in list(self.dict.keys()):
            return self.dict[name]

        else:
            return None
