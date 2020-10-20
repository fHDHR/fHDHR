import json


class Lineup_JSON():
    lineup_json = None

    def __init__(self, settings, device):
        self.config = settings
        self.device = device

    def get_lineup_json(self, base_url, force_update=False):
        if not self.lineup_json or force_update:
            jsonlineup = self.device.channels.get_station_list(base_url)
            self.lineup_json = json.dumps(jsonlineup, indent=4)

        return self.lineup_json
