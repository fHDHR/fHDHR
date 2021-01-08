from flask import request, redirect, Response
import urllib.parse
import json


class Cluster():
    endpoints = ["/api/cluster"]
    endpoint_name = "api_cluster"
    endpoint_methods = ["GET", "POST"]
    endpoint_default_parameters = {
                                    "method": "get"
                                    }

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        method = request.args.get('method', default="get", type=str)
        location = request.args.get("location", default=None, type=str)
        redirect_url = request.args.get('redirect', default=None, type=str)

        if method == "get":
            jsoncluster = self.fhdhr.device.cluster.cluster()
            cluster_json = json.dumps(jsoncluster, indent=4)

            return Response(status=200,
                            response=cluster_json,
                            mimetype='application/json')

        elif method == "scan":
            self.fhdhr.device.ssdp.m_search()

        elif method == 'add':
            self.fhdhr.device.cluster.add(location)
        elif method == 'del':
            self.fhdhr.device.cluster.remove(location)

        elif method == 'sync':
            self.fhdhr.device.cluster.sync(location)

        elif method == 'leave':
            self.fhdhr.device.cluster.leave()
        elif method == 'disconnect':
            self.fhdhr.device.cluster.disconnect()

        elif method == 'alive':
            self.fhdhr.device.ssdp.do_alive(forcealive=True)

        else:
            return "Invalid Method"

        if redirect_url:
            return redirect(redirect_url + "?retmessage=" + urllib.parse.quote("%s Success" % method))
        else:
            return "%s Success" % method
