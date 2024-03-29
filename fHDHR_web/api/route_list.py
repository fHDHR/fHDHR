from flask import Response, request, redirect, session
import urllib.parse
import json


class Route_List():
    endpoints = ["/api/routes"]
    endpoint_name = "api_routes"
    endpoint_methods = ["GET", "POST"]

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.handler(*args)

    def handler(self, *args):

        method = request.args.get('method', default="get", type=str)

        redirect_url = request.args.get('redirect', default=None, type=str)

        if method == "get":

            return_json = json.dumps(session["route_list"], indent=4)

            return Response(status=200,
                            response=return_json,
                            mimetype='application/json')

        else:
            return "%s Invalid Method" % method

        if redirect_url:
            if "?" in redirect_url:
                return redirect("%s&retmessage=%s" % (redirect_url, urllib.parse.quote("%s Success" % method)))
            else:
                return redirect("%s?retmessage=%s" % (redirect_url, urllib.parse.quote("%s Success" % method)))
        else:
            return "%s Success" % method
