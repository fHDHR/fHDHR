from flask import Response
import json


class Plugins_JSON():
    endpoints = ["/api/plugins"]
    endpoint_name = "api_plugins"
    endpoint_methods = ["GET", "POST"]

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

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
