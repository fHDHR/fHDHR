from flask import Response, request, redirect
import urllib.parse
import json


class EPG():
    """Methods to create xmltv.xml"""
    endpoints = ["/api/epg"]
    endpoint_name = "api_epg"
    endpoint_methods = ["GET", "POST"]

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        method = request.args.get('method', default="get", type=str)

        source = request.args.get('source', default=self.fhdhr.config.dict["epg"]["def_method"], type=str)
        if source not in self.fhdhr.config.dict["epg"]["valid_epg_methods"]:
            return "%s Invalid xmltv method" % source

        redirect_url = request.args.get('redirect', default=None, type=str)

        if method == "get":

            epgdict = self.fhdhr.device.epg.get_epg(source)
            if source in ["blocks", "origin", self.fhdhr.config.dict["main"]["dictpopname"]]:
                epgdict = epgdict.copy()
                for c in list(epgdict.keys()):
                    chan_obj = self.fhdhr.device.channels.get_channel_obj("origin_id", epgdict[c]["id"])
                    epgdict[chan_obj.number] = epgdict.pop(c)
                    epgdict[chan_obj.number]["name"] = chan_obj.dict["name"]
                    epgdict[chan_obj.number]["callsign"] = chan_obj.dict["callsign"]
                    epgdict[chan_obj.number]["number"] = chan_obj.number
                    epgdict[chan_obj.number]["id"] = chan_obj.dict["origin_id"]
                    epgdict[chan_obj.number]["thumbnail"] = chan_obj.thumbnail

            epg_json = json.dumps(epgdict, indent=4)

            return Response(status=200,
                            response=epg_json,
                            mimetype='application/json')

        elif method == "update":
            self.fhdhr.device.epg.update(source)

        elif method == "clearcache":
            self.fhdhr.device.epg.clear_epg_cache(source)

        else:
            return "%s Invalid Method" % method

        if redirect_url:
            return redirect("%s?retmessage=%s" % (redirect_url, urllib.parse.quote("%s Success" % method)))
        else:
            return "%s Success" % method
