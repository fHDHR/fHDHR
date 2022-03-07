from flask import Response, request, redirect
import urllib.parse
import json


class Plugins():
    endpoints = ["/api/plugins"]
    endpoint_name = "api_plugins"
    endpoint_methods = ["GET", "POST"]

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.handler(*args)

    def handler(self, *args):

        method = request.args.get('method', default=None, type=str)
        redirect_url = request.args.get('redirect', default=None, type=str)

        if method == "get":
            pluginsjson = {}

            for plugin in list(self.fhdhr.plugins.plugins.keys()):
                pluginsjson[plugin] = {
                                        "name": plugin,
                                        "manifest": self.fhdhr.plugins.plugins[plugin].manifest
                                        }

            plugins_json = json.dumps(pluginsjson, indent=4)

            return Response(status=200,
                            response=plugins_json,
                            mimetype='application/json')

        else:
            return "Invalid Method"

        if redirect_url:
            if "?" in redirect_url:
                return redirect("%s&retmessage=%s" % (redirect_url, urllib.parse.quote("%s Success" % method)))
            else:
                return redirect("%s?retmessage=%s" % (redirect_url, urllib.parse.quote("%s Success" % method)))
        else:
            return "%s Success" % method
