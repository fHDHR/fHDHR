import json


class Debug_JSON():

    def __init__(self, settings, device):
        self.config = settings
        self.device = device

    def get_debug_json(self, base_url):
        debugjson = {
                    "base_url": base_url,
                    "total channels": self.device.channels.get_station_total(),
                    "tuner status": self.device.tuners.status(),
                    }
        return json.dumps(debugjson, indent=4)
