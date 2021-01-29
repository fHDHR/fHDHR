from flask import Response, request
import json


class Discover_JSON():
    endpoints = ["/discover.json", "/hdhr/discover.json"]
    endpoint_name = "hdhr_discover_json"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    @property
    def source(self):
        return self.fhdhr.config.dict["hdhr"]["source"] or self.fhdhr.origins.valid_origins[0]

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        base_url = request.url_root[:-1]

        origin = self.source

        jsondiscover = {
                            "FriendlyName": "%s %s" % (self.fhdhr.config.dict["fhdhr"]["friendlyname"], origin),
                            "Manufacturer": self.fhdhr.config.dict["hdhr"]["reporting_manufacturer"],
                            "ModelNumber": self.fhdhr.config.dict["hdhr"]["reporting_model"],
                            "FirmwareName": self.fhdhr.config.dict["hdhr"]["reporting_firmware_name"],
                            "TunerCount": self.fhdhr.origins.origins_dict[origin].tuners,
                            "FirmwareVersion": self.fhdhr.config.dict["hdhr"]["reporting_firmware_ver"],
                            "DeviceID": "%s%s" % (self.fhdhr.config.dict["main"]["uuid"], origin),
                            "DeviceAuth": self.fhdhr.config.dict["fhdhr"]["device_auth"],
                            "BaseURL": "%s/hdhr" % base_url,
                            "LineupURL": "%s/hdhr/lineup.json" % base_url
                        }
        discover_json = json.dumps(jsondiscover, indent=4)

        return Response(status=200,
                        response=discover_json,
                        mimetype='application/json')
