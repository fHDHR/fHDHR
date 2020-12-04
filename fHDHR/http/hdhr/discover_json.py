from flask import Response, request
import json


class Discover_JSON():
    endpoints = ["/discover.json", "/hdhr/discover.json"]
    endpoint_name = "hdhr_discover_json"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        base_url = request.url_root[:-1]

        jsondiscover = {
                            "FriendlyName": self.fhdhr.config.dict["fhdhr"]["friendlyname"],
                            "Manufacturer": self.fhdhr.config.dict["fhdhr"]["reporting_manufacturer"],
                            "ModelNumber": self.fhdhr.config.dict["fhdhr"]["reporting_model"],
                            "FirmwareName": self.fhdhr.config.dict["fhdhr"]["reporting_firmware_name"],
                            "TunerCount": self.fhdhr.config.dict["fhdhr"]["tuner_count"],
                            "FirmwareVersion": self.fhdhr.config.dict["fhdhr"]["reporting_firmware_ver"],
                            "DeviceID": self.fhdhr.config.dict["main"]["uuid"],
                            "DeviceAuth": self.fhdhr.config.dict["fhdhr"]["device_auth"],
                            "BaseURL": "%s" % base_url,
                            "LineupURL": "%s/lineup.json" % base_url
                        }
        discover_json = json.dumps(jsondiscover, indent=4)

        return Response(status=200,
                        response=discover_json,
                        mimetype='application/json')
