import os
import json
import urllib.parse
import requests
from collections import OrderedDict


class fHDHR_Cluster():

    def __init__(self, settings, ssdp):
        self.config = settings
        self.ssdp = ssdp
        self.cluster_file = self.config.dict["main"]["cluster"]
        self.friendlyname = self.config.dict["fhdhr"]["friendlyname"]
        self.location = ('http://' + settings.dict["fhdhr"]["discovery_address"] + ':' +
                         str(settings.dict["fhdhr"]["port"]))
        self.location_url = urllib.parse.quote(self.location)
        self.cluster = self.default_cluster()
        self.load_cluster()
        self.startup_sync()

    def get_list(self):
        return_dict = {}
        for location in list(self.cluster.keys()):
            if location != self.location:
                return_dict[location] = {
                                        "Joined": True
                                        }

        detected_list = self.ssdp.detect_method.get()
        for location in detected_list:
            if location not in list(self.cluster.keys()):
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

    def load_cluster(self):
        if os.path.isfile(self.cluster_file):
            with open(self.cluster_file, 'r') as clusterfile:
                self.cluster = json.load(clusterfile)
            if self.location not in list(self.cluster.keys()):
                self.cluster[self.location] = self.default_cluster()[self.location]
        else:
            self.cluster = self.default_cluster()

    def startup_sync(self):
        for location in list(self.cluster.keys()):
            if location != self.location:
                sync_url = location + "/cluster.json"
                try:
                    sync_open = requests.get(sync_url)
                    retrieved_cluster = sync_open.json()
                    if self.location not in list(retrieved_cluster.keys()):
                        return self.leave()
                except requests.exceptions.ConnectionError:
                    print("Unreachable: " + location)

    def save_cluster(self):
        with open(self.cluster_file, 'w') as clusterfile:
            clusterfile.write(json.dumps(self.cluster, indent=4))

    def leave(self):
        self.cluster = self.default_cluster()
        self.save_cluster()

    def disconnect(self):
        for location in list(self.cluster.keys()):
            if location != self.location:
                sync_url = location + "/cluster?method=del&location=" + self.location
                try:
                    requests.get(sync_url)
                except requests.exceptions.ConnectionError:
                    print("Unreachable: " + location)
        self.leave()

    def sync(self, location):
        sync_url = location + "/cluster.json"
        try:
            sync_open = requests.get(sync_url)
            self.cluster = sync_open.json()
            self.save_cluster()
        except requests.exceptions.ConnectionError:
            print("Unreachable: " + location)

    def push_sync(self):
        for location in list(self.cluster.keys()):
            if location != self.location:
                sync_url = location + "/cluster?method=sync&location=" + self.location_url
                try:
                    requests.get(sync_url)
                except requests.exceptions.ConnectionError:
                    print("Unreachable: " + location)

    def add(self, location):
        if location not in list(self.cluster.keys()):
            self.cluster[location] = {"base_url": location}

            location_info_url = location + "/discover.json"
            try:
                location_info_req = requests.get(location_info_url)
            except requests.exceptions.ConnectionError:
                print("Unreachable: " + location)
                del self.cluster[location]
                return
            location_info = location_info_req.json()
            self.cluster[location]["name"] = location_info["FriendlyName"]

            cluster_info_url = location + "/cluster.json"
            try:
                cluster_info_req = requests.get(cluster_info_url)
            except requests.exceptions.ConnectionError:
                print("Unreachable: " + location)
                del self.cluster[location]
                return
            cluster_info = cluster_info_req.json()
            for cluster_key in list(cluster_info.keys()):
                if cluster_key not in list(self.cluster.keys()):
                    self.cluster[cluster_key] = cluster_info[cluster_key]

            self.push_sync()
            self.save_cluster()

    def remove(self, location):
        if location in list(self.cluster.keys()):
            del self.cluster[location]
            sync_url = location + "/cluster?method=leave"
            try:
                requests.get(sync_url)
            except requests.exceptions.ConnectionError:
                print("Unreachable: " + location)
            self.push_sync()
            self.save_cluster()
