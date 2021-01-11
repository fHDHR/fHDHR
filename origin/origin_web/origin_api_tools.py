from flask import Response, request, redirect
import urllib.parse
import json


class Origin_API_Tools():
    endpoints = ["/api/origin/tools"]
    endpoint_name = "api_origin_tools"
    endpoint_methods = ["GET", "POST"]

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        method = request.args.get('method', default="get", type=str)

        redirect_url = request.args.get('redirect', default=None, type=str)

        if method == "channels":

            dma = request.args.get('dma', default=self.fhdhr.originwrapper.originservice.location["DMA"], type=str)
            stations_url = 'https://api.locastnet.org/api/watch/epg/%s' % dma

            try:
                stationsReq = self.fhdhr.web.session.get(stations_url)
                stationsReq.raise_for_status()
                stationsRes = stationsReq.json()
            except self.fhdhr.web.exceptions.HTTPError as err:
                self.fhdhr.logger.error('Error while getting stations: %s' % err)
                stationsRes = [{"error": 'Error while getting stations: %s' % err, "listings": []}]

            filtered_json = []
            for station_item in stationsRes:
                station_item["listings"] = []
                filtered_json.append(station_item)

            stations_json = json.dumps(filtered_json, indent=4)

            return Response(status=200,
                            response=stations_json,
                            mimetype='application/json')

        elif method == "zipcode":

            zipcode = request.args.get('zipcode', default=None, type=str)
            if not zipcode:
                if redirect_url:
                    return redirect("%s?retmessage=%s" % (redirect_url, urllib.parse.quote("%s Success" % method)))
                else:
                    return "%s Success" % method

            status_url = 'https://api.locastnet.org/api/watch/dma/zip/%s' % zipcode

            try:
                statusReq = self.fhdhr.web.session.get(status_url)
                statusReq.raise_for_status()
                statusRes = statusReq.json()
            except self.fhdhr.web.exceptions.HTTPError as err:
                self.fhdhr.logger.error('Error while getting zipcode status: %s' % err)
                statusRes = [{"error": 'Error while getting zipcode status: %s' % err, "listings": []}]

            status_json = json.dumps(statusRes, indent=4)

            return Response(status=200,
                            response=status_json,
                            mimetype='application/json')

        else:
            return "%s Invalid Method" % method

        if redirect_url:
            return redirect("%s?retmessage=%s" % (redirect_url, urllib.parse.quote("%s Success" % method)))
        else:
            return "%s Success" % method
