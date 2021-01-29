from flask import request, Response
import json


class Debug_JSON():
    endpoints = ["/api/debug"]
    endpoint_name = "api_debug"
    endpoint_methods = ["GET", "POST"]

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        base_url = request.url_root[:-1]

        debugjson = {
                    "base_url": base_url,
                    }

        for origin in list(self.fhdhr.origins.origins_dict.keys()):
            debugjson[origin] = {
                                "tuner status": self.fhdhr.device.tuners.status(origin),
                                "total channels": len(list(self.fhdhr.device.channels.list[origin].keys()))
                                }

        debug_json = json.dumps(debugjson, indent=4)

        return Response(status=200,
                        response=debug_json,
                        mimetype='application/json')
