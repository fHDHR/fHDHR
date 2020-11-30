from flask import Response, request
import json


class Lineup_JSON():
    endpoints = ["/lineup.json"]
    endpoint_name = "file_lineup_json"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        base_url = request.url_root[:-1]

        show = request.args.get('show', default="all", type=str)

        jsonlineup = []
        for fhdhr_id in list(self.fhdhr.device.channels.list.keys()):
            channel_obj = self.fhdhr.device.channels.list[fhdhr_id]
            if channel_obj.enabled or show == "found":
                lineup_dict = channel_obj.lineup_dict()
                lineup_dict["URL"] = base_url + lineup_dict["URL"]
                if show == "found" and channel_obj.enabled:
                    lineup_dict["Enabled"] = 1
                elif show == "found" and not channel_obj.enabled:
                    lineup_dict["Enabled"] = 0
                jsonlineup.append(lineup_dict)

        lineup_json = json.dumps(jsonlineup, indent=4)

        return Response(status=200,
                        response=lineup_json,
                        mimetype='application/json')
