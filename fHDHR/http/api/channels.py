from flask import request, redirect
import urllib.parse


class Channels():
    endpoints = ["/api/channels"]
    endpoint_name = "api_channels"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        method = request.args.get('method', default=None, type=str)
        redirect_url = request.args.get('redirect', default=None, type=str)

        if method == "scan":
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
