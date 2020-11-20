from flask import request, redirect, Response
import urllib.parse
import json


class Channels():
    endpoints = ["/api/channels"]
    endpoint_name = "api_channels"
    endpoint_methods = ["GET", "POST"]

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        method = request.args.get('method', default=None, type=str)
        redirect_url = request.args.get('redirect', default=None, type=str)

        if method == "get":
            channels_info = []
            for fhdhr_id in list(self.fhdhr.device.channels.list.keys()):
                channel_obj = self.fhdhr.device.channels.list[fhdhr_id]
                channel_dict = channel_obj.dict.copy()
                channel_dict["play_url"] = channel_obj.play_url()
                channel_dict["stream_url"] = channel_obj.stream_url()
                channels_info.append(channel_dict)
            channels_info_json = json.dumps(channels_info, indent=4)

            return Response(status=200,
                            response=channels_info_json,
                            mimetype='application/json')

        elif method in ["enable", "disable"]:
            channel = request.args.get('channel', default=None, type=str)
            if not channel:
                if redirect_url:
                    return redirect(redirect_url + "?retmessage=" + urllib.parse.quote("%s Failed" % method))
                else:
                    return "%s Falied" % method
            self.fhdhr.device.channels.set_channel_status("number", channel, method)

        elif method == "scan":
            self.fhdhr.device.station_scan.scan()

        else:
            return "Invalid Method"

        if redirect_url:
            return redirect(redirect_url + "?retmessage=" + urllib.parse.quote("%s Success" % method))
        else:
            if method == "scan":
                return redirect('/lineup_status.json')
            else:
                return "%s Success" % method
