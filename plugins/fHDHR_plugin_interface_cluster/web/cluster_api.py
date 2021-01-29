from flask import request, redirect, Response
import urllib.parse
import json


class Cluster_API():
    endpoints = ["/api/cluster"]
    endpoint_name = "api_cluster"
    endpoint_methods = ["GET", "POST"]
    endpoint_default_parameters = {
                                    "method": "get"
                                    }

    def __init__(self, fhdhr, plugin_utils):
        self.fhdhr = fhdhr
        self.plugin_utils = plugin_utils

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        method = request.args.get('method', default="get", type=str)
        location = request.args.get("location", default=None, type=str)
        redirect_url = request.args.get('redirect', default=None, type=str)

        if method == "get":
            jsoncluster = self.fhdhr.device.interfaces[self.plugin_utils.namespace].cluster()
            cluster_json = json.dumps(jsoncluster, indent=4)

            return Response(status=200,
                            response=cluster_json,
                            mimetype='application/json')

        elif method == "ident":
            jsoncluster = {
                            "name": self.fhdhr.config.dict["cluster"]["friendlyname"] or "%s %s" % (self.fhdhr.config.dict["fhdhr"]["friendlyname"], self.fhdhr.origins.valid_origins[0])
                            }

            cluster_json = json.dumps(jsoncluster, indent=4)

            return Response(status=200,
                            response=cluster_json,
                            mimetype='application/json')

        elif method == "scan":
            self.fhdhr.device.ssdp.m_search()

        elif method == 'add':
            self.fhdhr.device.interfaces[self.plugin_utils.namespace].add(location)
        elif method == 'del':
            self.fhdhr.device.interfaces[self.plugin_utils.namespace].remove(location)

        elif method == 'sync':
            self.fhdhr.device.interfaces[self.plugin_utils.namespace].sync(location)

        elif method == 'leave':
            self.fhdhr.device.interfaces[self.plugin_utils.namespace].leave()
        elif method == 'disconnect':
            self.fhdhr.device.interfaces[self.plugin_utils.namespace].disconnect()

        elif method == 'alive':
            self.fhdhr.device.ssdp.do_alive(forcealive=True)

        else:
            return "Invalid Method"

        if redirect_url:
            return redirect("%s?retmessage=%s" % (redirect_url, urllib.parse.quote("%s Success" % method)))
        else:
            return "%s Success" % method
