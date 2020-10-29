import json


class Cluster_JSON():

    def __init__(self, settings, device):
        self.config = settings
        self.device = device

    def get_cluster_json(self, base_url, force_update=False):
        jsoncluster = self.device.cluster.cluster
        cluster_json = json.dumps(jsoncluster, indent=4)
        return cluster_json
