

class Channel():

    def __init__(self, fhdhr, id_system, origin_id=None, channel_id=None):
        self.fhdhr = fhdhr

        self.id_system = id_system

        if not channel_id:
            if origin_id:
                channel_id = id_system.get(origin_id)
            else:
                channel_id = id_system.assign()
        self.dict = self.fhdhr.db.get_channel_value(str(channel_id), "dict") or self.default_dict(channel_id)
        self.verify_dict()
        self.fhdhr.db.set_channel_value(self.dict["id"], "dict", self.dict)

    def verify_dict(self):
        """Development Purposes
        Add new Channel dict keys
        """
        default_dict = self.default_dict(self.dict["id"])
        for key in list(default_dict.keys()):
            if key not in list(self.dict.keys()):
                self.dict[key] = default_dict[key]

    def basics(self, channel_info):
        """Some Channel Information is Critical"""

        if "name" not in list(channel_info.keys()):
            channel_info["name"] = self.dict["id"]
        self.dict["origin_name"] = channel_info["name"]
        if not self.dict["name"]:
            self.dict["name"] = self.dict["origin_name"]

        if "id" not in list(channel_info.keys()):
            channel_info["id"] = channel_info["name"]
        self.dict["origin_id"] = channel_info["id"]

        if "callsign" not in list(channel_info.keys()):
            channel_info["callsign"] = channel_info["name"]
        self.dict["origin_callsign"] = channel_info["callsign"]
        if not self.dict["callsign"]:
            self.dict["callsign"] = self.dict["origin_callsign"]

        if "tags" not in list(channel_info.keys()):
            channel_info["tags"] = []
        self.dict["origin_tags"] = channel_info["tags"]
        if not self.dict["tags"]:
            self.dict["tags"] = self.dict["origin_tags"]

        if "number" not in list(channel_info.keys()):
            channel_info["number"] = self.id_system.get_number(channel_info["id"])
        self.dict["origin_number"] = str(float(channel_info["number"]))
        if not self.dict["number"]:
            self.dict["number"] = self.dict["origin_number"]

        if "thumbnail" not in list(channel_info.keys()):
            channel_info["thumbnail"] = None
        self.dict["origin_thumbnail"] = channel_info["thumbnail"]
        if not self.dict["thumbnail"]:
            self.dict["thumbnail"] = self.dict["origin_thumbnail"]

        if "HD" not in list(channel_info.keys()):
            channel_info["HD"] = 0
        self.dict["HD"] = channel_info["HD"]

        self.fhdhr.db.set_channel_value(self.dict["id"], "dict", self.dict)

    def default_dict(self, channel_id):
        return {
                "id": str(channel_id), "origin_id": None,
                "name": None, "origin_name": None,
                "callsign": None, "origin_callsign": None,
                "number": None, "origin_number": None,
                "tags": [], "origin_tags": [],
                "thumbnail": None, "origin_thumbnail": None,
                "enabled": True, "favorite": 0,
                "HD": 0,
                }

    def destroy(self):
        self.fhdhr.db.delete_channel_value(self.dict["id"], "dict")
        channel_ids = self.fhdhr.db.get_fhdhr_value("channels", "list") or []
        if self.dict["id"] in channel_ids:
            channel_ids.remove(self.dict["id"])
        self.fhdhr.db.set_fhdhr_value("channels", "list", channel_ids)

    def set_status(self, updatedict):
        for key in list(updatedict.keys()):
            if key == "number":
                updatedict[key] = str(float(updatedict[key]))
            self.dict[key] = updatedict[key]
        self.fhdhr.db.set_channel_value(self.dict["id"], "dict", self.dict)

    def lineup_dict(self):
        return {
                 'GuideNumber': self.dict['number'],
                 'GuideName': self.dict['name'],
                 'Tags': ",".join(self.dict['tags']),
                 'URL': self.stream_url(),
                 'HD': self.dict["HD"],
                 "Favorite": self.dict["favorite"],
                }

    def stream_url(self):
        return ('/auto/v%s' % self.dict['number'])

    def play_url(self):
        return ('/api/m3u?method=get&channel=%s' % self.dict['number'])

    def set_favorite(self, enablement):
        if enablement == "+":
            self.dict["favorite"] = 1
        elif enablement == "+":
            self.dict["favorite"] = 0
        self.fhdhr.db.set_channel_value(self.dict["id"], "info", self.dict)

    def set_enablement(self, enablement):
        if enablement == "disable":
            self.dict["enabled"] = False
        elif enablement == "enable":
            self.dict["enabled"] = True
        elif enablement == "toggle":
            if self.dict["enabled"]:
                self.dict["enabled"] = False
            else:
                self.dict["enabled"] = True
        self.fhdhr.db.set_channel_value(self.dict["id"], "info", self.dict)

    def __getattr__(self, name):
        ''' will only get called for undefined attributes '''
        if name in list(self.dict.keys()):
            return self.dict[name]
        else:
            return None
