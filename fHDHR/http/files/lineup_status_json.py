from flask import Response
import json


class Lineup_Status_JSON():
    endpoints = ["/lineup_status.json"]
    endpoint_name = "lineup_status_json"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        station_scanning = self.fhdhr.device.station_scan.scanning()
        if station_scanning:
            jsonlineup = self.scan_in_progress()
        elif not self.fhdhr.device.channels.get_station_total():
            jsonlineup = self.scan_in_progress()
        else:
            jsonlineup = self.not_scanning()
        lineup_json = json.dumps(jsonlineup, indent=4)

        return Response(status=200,
                        response=lineup_json,
                        mimetype='application/json')

    def scan_in_progress(self):
        channel_count = self.fhdhr.device.channels.get_station_total()
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
                      "Source": self.fhdhr.config.dict["fhdhr"]["reporting_tuner_type"],
                      "SourceList": [self.fhdhr.config.dict["fhdhr"]["reporting_tuner_type"]],
                      }
        return jsonlineup
