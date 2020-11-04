import urllib.parse
from collections import OrderedDict


class fHDHR_Cluster():

    def __init__(self, settings, ssdp, logger, db,  web):
        self.config = settings
        self.logger = logger
        self.ssdp = ssdp
        self.db = db
        self.web = web

        self.friendlyname = self.config.dict["fhdhr"]["friendlyname"]
        self.location = None
        self.location_url = None
        if settings.dict["fhdhr"]["discovery_address"]:
            self.location = ('http://' + settings.dict["fhdhr"]["discovery_address"] + ':' +
                             str(settings.dict["fhdhr"]["port"]))
            self.location_url = urllib.parse.quote(self.location)

            self.startup_sync()

    def cluster(self):
        return self.db.get_fhdhr_value("cluster", "dict") or self.default_cluster()

    def get_list(self):
        cluster = self.db.get_fhdhr_value("cluster", "dict") or self.default_cluster()
        return_dict = {}
        for location in list(cluster.keys()):
            if location != self.location:
                return_dict[location] = {
                                        "Joined": True
                                        }

        detected_list = self.ssdp.detect_method.get()
        for location in detected_list:
            if location not in list(cluster.keys()):
                return_dict[location] = {
                                        "Joined": False
                                        }
        return_dict = OrderedDict(sorted(return_dict.items()))
        return return_dict

    def default_cluster(self):
        defdict = {}
        defdict[self.location] = {
                                "base_url": self.location,
                                "name": self.friendlyname
                                }
        return defdict

    def startup_sync(self):
        cluster = self.db.get_fhdhr_value("cluster", "dict") or self.default_cluster()
        for location in list(cluster.keys()):
            if location != self.location:
                sync_url = location + "/api/cluster?method=get"
                try:
                    sync_open = self.web.session.get(sync_url)
                    retrieved_cluster = sync_open.json()
                    if self.location not in list(retrieved_cluster.keys()):
                        return self.leave()
                except self.web.exceptions.ConnectionError:
                    self.logger.error("Unreachable: " + location)

    def leave(self):
        self.db.set_fhdhr_value("cluster", "dict", self.default_cluster())

    def disconnect(self):
        cluster = self.db.get_fhdhr_value("cluster", "dict") or self.default_cluster()
        for location in list(cluster.keys()):
            if location != self.location:
                sync_url = location + "/api/cluster?method=del&location=" + self.location
                try:
                    self.web.session.get(sync_url)
                except self.web.exceptions.ConnectionError:
                    self.logger.error("Unreachable: " + location)
        self.leave()

    def sync(self, location):
        sync_url = location + "/api/cluster?method=get"
        try:
            sync_open = self.web.session.get(sync_url)
            self.db.set_fhdhr_value("cluster", "dict", sync_open.json())
        except self.web.exceptions.ConnectionError:
            self.logger.error("Unreachable: " + location)

    def push_sync(self):
        cluster = self.db.get_fhdhr_value("cluster", "dict") or self.default_cluster()
        for location in list(cluster.keys()):
            if location != self.location:
                sync_url = location + "/api/cluster?method=sync&location=" + self.location_url
                try:
                    self.web.session.get(sync_url)
                except self.web.exceptions.ConnectionError:
                    self.logger.error("Unreachable: " + location)

    def add(self, location):
        cluster = self.db.get_fhdhr_value("cluster", "dict") or self.default_cluster()
        if location not in list(cluster.keys()):
            cluster[location] = {"base_url": location}

            location_info_url = location + "/discover.json"
            try:
                location_info_req = self.web.session.get(location_info_url)
            except self.web.exceptions.ConnectionError:
                self.logger.error("Unreachable: " + location)
                del cluster[location]
                self.db.set_fhdhr_value("cluster", "dict", cluster)
                return
            location_info = location_info_req.json()
            cluster[location]["name"] = location_info["FriendlyName"]

            cluster_info_url = location + "/api/cluster?method=get"
            try:
                cluster_info_req = self.web.session.get(cluster_info_url)
            except self.web.exceptions.ConnectionError:
                self.logger.error("Unreachable: " + location)
                del cluster[location]
                self.db.set_fhdhr_value("cluster", "dict", cluster)
                return
            cluster_info = cluster_info_req.json()
            for cluster_key in list(cluster_info.keys()):
                if cluster_key not in list(cluster.keys()):
                    cluster[cluster_key] = cluster_info[cluster_key]

            self.db.set_fhdhr_value("cluster", "dict", cluster)
            self.push_sync()

    def remove(self, location):
        cluster = self.db.get_fhdhr_value("cluster", "dict") or self.default_cluster()
        if location in list(cluster.keys()):
            del cluster[location]
            sync_url = location + "/api/cluster?method=leave"
            try:
                self.web.session.get(sync_url)
            except self.web.exceptions.ConnectionError:
                self.logger.error("Unreachable: " + location)
            self.push_sync()
            self.db.set_fhdhr_value("cluster", "dict", cluster)
