import json


class Lineup_Status_JSON():

    def __init__(self, settings, origserv):
        self.config = settings
        self.origserv = origserv

    def get_lineup_json(self, station_scanning):
        if station_scanning:
            jsonlineup = self.scan_in_progress()
        elif not self.origserv.get_station_total():
            jsonlineup = self.scan_in_progress()
        else:
            jsonlineup = self.not_scanning()
        return json.dumps(jsonlineup, indent=4)

    def scan_in_progress(self):
        channel_count = self.origserv.get_station_total()
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
