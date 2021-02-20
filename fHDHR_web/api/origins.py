from flask import request, redirect, Response
import urllib.parse
import json


class Origins():
    endpoints = ["/api/origins"]
    endpoint_name = "api_origins"
    endpoint_methods = ["GET", "POST"]
    endpoint_default_parameters = {
                                    "method": "get"
                                    }

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        method = request.args.get('method', default=None, type=str)
        redirect_url = request.args.get('redirect', default=None, type=str)

        if method == "get":
            origins_info = {}

            for origin_item in self.fhdhr.origins.valid_origins:

                origins_info[origin_item] = {}

                origins_info[origin_item]["tuners_max"] = self.fhdhr.origins.origins_dict[origin_item].tuners
                origins_info[origin_item]["channel_count"] = len(list(self.fhdhr.device.channels.list[origin_item].keys()))
                origins_info[origin_item]["stream_method"] = self.fhdhr.origins.origins_dict[origin_item].stream_method

                if hasattr(self.fhdhr.origins.origins_dict[origin_item], "close_stream"):
                    origins_info[origin_item]["close_stream_method"] = True
                else:
                    origins_info[origin_item]["close_stream_method"] = False

            origins_info_json = json.dumps(origins_info, indent=4)

            return Response(status=200,
                            response=origins_info_json,
                            mimetype='application/json')

        else:
            return "Invalid Method"

        if redirect_url:
            if "?" in redirect_url:
                return redirect("%s&retmessage=%s" % (redirect_url, urllib.parse.quote("%s Success" % method)))
            else:
                return redirect("%s?retmessage=%s" % (redirect_url, urllib.parse.quote("%s Success" % method)))
        else:
            if method == "scan":
                return redirect('/lineup_status.json')
            else:
                return "%s Success" % method
