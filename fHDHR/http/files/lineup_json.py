from flask import Response, request
import json


class Lineup_JSON():
    endpoints = ["/lineup.json"]
    endpoint_name = "lineup_json"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        base_url = request.url_root[:-1]

        jsonlineup = self.fhdhr.device.channels.get_station_list(base_url)
        lineup_json = json.dumps(jsonlineup, indent=4)

        return Response(status=200,
                        response=lineup_json,
                        mimetype='application/json')
