import json


class Discover_JSON():
    discover_json = None

    def __init__(self, settings):
        self.config = settings

    def get_discover_json(self, base_url, force_update=False):
        if not self.discover_json or force_update:
            jsondiscover = {
                                "FriendlyName": self.config.dict["fhdhr"]["friendlyname"],
                                "Manufacturer": self.config.dict["dev"]["reporting_manufacturer"],
                                "ModelNumber": self.config.dict["dev"]["reporting_model"],
                                "FirmwareName": self.config.dict["dev"]["reporting_firmware_name"],
                                "TunerCount": self.config.dict["fhdhr"]["tuner_count"],
                                "FirmwareVersion": self.config.dict["dev"]["reporting_firmware_ver"],
                                "DeviceID": self.config.dict["main"]["uuid"],
                                "DeviceAuth": "fHDHR",
                                "BaseURL": "http://" + base_url,
                                "LineupURL": "http://" + base_url + "/lineup.json"
                            }
            self.discover_json = json.dumps(jsondiscover, indent=4)

        return self.discover_json
