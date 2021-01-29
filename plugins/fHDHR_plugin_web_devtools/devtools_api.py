from flask import Response, request, redirect
import urllib.parse
import json


class DevTools_API():
    endpoints = ["/api/devtools"]
    endpoint_name = "api_devtools"
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

        redirect_url = request.args.get('redirect', default=None, type=str)

        if method == "get":

            return_json = json.dumps({"tools": "api for tools page"}, indent=4)

            return Response(status=200,
                            response=return_json,
                            mimetype='application/json')

        elif method == "prettyjson":

            dirty_json_url = request.form.get('url', None)

            try:
                json_url_req = self.plugin_utils.web.session.get(dirty_json_url)
                json_url_req.raise_for_status()
                json_resp = json_url_req.json()
            except self.plugin_utilsplugin_utils.web.exceptions.HTTPError as err:
                self.plugin_utils.logger.error('Error while getting stations: %s' % err)
                json_resp = {"error": 'Error while getting stations: %s' % err}

            return_json = json.dumps(json_resp, indent=4)

            return Response(status=200,
                            response=return_json,
                            mimetype='application/json')

        else:
            return "%s Invalid Method" % method

        if redirect_url:
            return redirect("%s?retmessage=%s" % (redirect_url, urllib.parse.quote("%s Success" % method)))
        else:
            return "%s Success" % method
