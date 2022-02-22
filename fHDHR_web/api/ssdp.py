from flask import request, redirect, Response
import urllib.parse
import json


class SSDP_API():
    endpoints = ["/api/ssdp"]
    endpoint_name = "api_ssdp"
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

            ssdp_methods_json = json.dumps(self.fhdhr.device.ssdp.methods, indent=4)

            return Response(status=200,
                            response=ssdp_methods_json,
                            mimetype='application/json')
        elif method == "scan":
            self.fhdhr.device.ssdp.m_search()

        elif method == 'alive':
            self.fhdhr.device.ssdp.do_alive()

        else:
            return "Invalid Method"

        if redirect_url:
            return redirect("%s?retmessage=%s" % (redirect_url, urllib.parse.quote("%s Success" % method)))
        else:
            return "%s Success" % method
