import json


class Lineup_Status_JSON():

    def __init__(self, settings, device):
        self.config = settings
        self.device = device

    def get_lineup_status_json(self):
        station_scanning = self.device.station_scan.scanning()
        if station_scanning:
            jsonlineup = self.scan_in_progress()
        elif not self.device.channels.get_station_total():
            jsonlineup = self.scan_in_progress()
        else:
            jsonlineup = self.not_scanning()
        return json.dumps(jsonlineup, indent=4)

    def scan_in_progress(self):
        channel_count = self.device.channels.get_station_total()
        jsonlineup = {
                      "ScanInProgress": "true",
                      "Progress": 99,
                      "Found": channel_count
                      }
        return jsonlineup

    def not_scanning(self):
        jsonlineup = {
                      "ScanInProgress": "false",
                      "ScanPossible": "true",
                      "Source": self.config.dict["dev"]["reporting_tuner_type"],
                      "SourceList": [self.config.dict["dev"]["reporting_tuner_type"]],
                      }
        return jsonlineup
