import urllib.parse
from collections import OrderedDict


class fHDHR_Cluster():

    def __init__(self, fhdhr, ssdp):
        self.fhdhr = fhdhr

        self.ssdp = ssdp

        self.friendlyname = self.fhdhr.config.dict["fhdhr"]["friendlyname"]
        self.location = None
        self.location_url = None
        if fhdhr.config.dict["fhdhr"]["discovery_address"]:
            self.location = ('http://' + fhdhr.config.dict["fhdhr"]["discovery_address"] + ':' +
                             str(fhdhr.config.dict["fhdhr"]["port"]))
            self.location_url = urllib.parse.quote(self.location)

            self.startup_sync()

    def cluster(self):
        return self.fhdhr.db.get_fhdhr_value("cluster", "dict") or self.default_cluster()

    def get_list(self):
        cluster = self.fhdhr.db.get_fhdhr_value("cluster", "dict") or self.default_cluster()
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
        cluster = self.fhdhr.db.get_fhdhr_value("cluster", "dict") or self.default_cluster()
        for location in list(cluster.keys()):
            if location != self.location:
                sync_url = location + "/api/cluster?method=get"
                try:
                    sync_open = self.fhdhr.web.session.get(sync_url)
                    retrieved_cluster = sync_open.json()
                    if self.location not in list(retrieved_cluster.keys()):
                        return self.leave()
                except self.fhdhr.web.exceptions.ConnectionError:
                    self.fhdhr.logger.error("Unreachable: " + location)

    def leave(self):
        self.fhdhr.db.set_fhdhr_value("cluster", "dict", self.default_cluster())

    def disconnect(self):
        cluster = self.fhdhr.db.get_fhdhr_value("cluster", "dict") or self.default_cluster()
        for location in list(cluster.keys()):
            if location != self.location:
                sync_url = location + "/api/cluster?method=del&location=" + self.location
                try:
                    self.fhdhr.web.session.get(sync_url)
                except self.fhdhr.web.exceptions.ConnectionError:
                    self.fhdhr.logger.error("Unreachable: " + location)
        self.leave()

    def sync(self, location):
        sync_url = location + "/api/cluster?method=get"
        try:
            sync_open = self.fhdhr.web.session.get(sync_url)
            self.fhdhr.db.set_fhdhr_value("cluster", "dict", sync_open.json())
        except self.fhdhr.web.exceptions.ConnectionError:
            self.fhdhr.logger.error("Unreachable: " + location)

    def push_sync(self):
        cluster = self.fhdhr.db.get_fhdhr_value("cluster", "dict") or self.default_cluster()
        for location in list(cluster.keys()):
            if location != self.location:
                sync_url = location + "/api/cluster?method=sync&location=" + self.location_url
                try:
                    self.fhdhr.web.session.get(sync_url)
                except self.fhdhr.web.exceptions.ConnectionError:
                    self.fhdhr.logger.error("Unreachable: " + location)

    def add(self, location):
        cluster = self.fhdhr.db.get_fhdhr_value("cluster", "dict") or self.default_cluster()
        if location not in list(cluster.keys()):
            cluster[location] = {"base_url": location}

            location_info_url = location + "/discover.json"
            try:
                location_info_req = self.fhdhr.web.session.get(location_info_url)
            except self.fhdhr.web.exceptions.ConnectionError:
                self.fhdhr.logger.error("Unreachable: " + location)
                del cluster[location]
                self.fhdhr.db.set_fhdhr_value("cluster", "dict", cluster)
                return
            location_info = location_info_req.json()
            cluster[location]["name"] = location_info["FriendlyName"]

            cluster_info_url = location + "/api/cluster?method=get"
            try:
                cluster_info_req = self.fhdhr.web.session.get(cluster_info_url)
            except self.fhdhr.web.exceptions.ConnectionError:
                self.fhdhr.logger.error("Unreachable: " + location)
                del cluster[location]
                self.fhdhr.db.set_fhdhr_value("cluster", "dict", cluster)
                return
            cluster_info = cluster_info_req.json()
            for cluster_key in list(cluster_info.keys()):
                if cluster_key not in list(cluster.keys()):
                    cluster[cluster_key] = cluster_info[cluster_key]

            self.fhdhr.db.set_fhdhr_value("cluster", "dict", cluster)
            self.push_sync()

    def remove(self, location):
        cluster = self.fhdhr.db.get_fhdhr_value("cluster", "dict") or self.default_cluster()
        if location in list(cluster.keys()):
            del cluster[location]
            sync_url = location + "/api/cluster?method=leave"
            try:
                self.fhdhr.web.session.get(sync_url)
            except self.fhdhr.web.exceptions.ConnectionError:
                self.fhdhr.logger.error("Unreachable: " + location)
            self.push_sync()
            self.fhdhr.db.set_fhdhr_value("cluster", "dict", cluster)
