from flask import request, redirect, Response
import urllib.parse
from io import StringIO
import json


class Logs():
    endpoints = ["/api/logs"]
    endpoint_name = "api_logs"
    endpoint_methods = ["GET", "POST"]

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        method = request.args.get('method', default="text", type=str)
        redirect_url = request.args.get('redirect', default=None, type=str)

        if method == "text":

            level = request.args.get('level', default=self.fhdhr.logger.levelname, type=str)
            limit = request.args.get('limit', default=None, type=str)

            logs = self.fhdhr.logger.memory.filter(level=level, limit=limit)

            fakefile = StringIO()

            for log_entry in list(logs.keys()):
                fakefile.write("%s\n" % self.fhdhr.logger.memory.dict[log_entry]["fmsg"])

            logfile = fakefile.getvalue()

            return Response(status=200, response=logfile, mimetype='text/plain')

        elif method == "json":

            level = request.args.get('level', default=self.fhdhr.logger.levelname, type=str)
            limit = request.args.get('limit', default=None, type=str)

            logs = self.fhdhr.logger.memory.filter(level=level, limit=limit)

            logs_json = json.dumps(logs, indent=4)

            return Response(status=200,
                            response=logs_json,
                            mimetype='application/json')

        if redirect_url:
            if "?" in redirect_url:
                return redirect("%s&retmessage=%s" % (redirect_url, urllib.parse.quote("%s Success" % method)))
            else:
                return redirect("%s?retmessage=%s" % (redirect_url, urllib.parse.quote("%s Success" % method)))
        else:
            return "%s Success" % method
