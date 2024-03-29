from flask import Response, request, redirect
import urllib.parse
import json

from fHDHR.tools import channel_sort


class W3U():
    endpoints = ["/api/w3u"]
    endpoint_name = "api_w3u"
    endpoint_methods = ["GET", "POST"]

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.handler(*args)

    def handler(self, *args):

        base_url = request.url_root[:-1]

        method = request.args.get('method', default="get", type=str)
        channel = request.args.get('channel', default="all", type=str)
        redirect_url = request.args.get('redirect', default=None, type=str)

        if method == "get":

            origin_methods = self.fhdhr.origins.list_origins
            origin_name = request.args.get('origin', default=None, type=str)
            if origin_name and origin_name not in origin_methods:
                return "%s Invalid channels origin" % origin_name

            channel_info_w3u = {
                                "name": self.fhdhr.config.dict["fhdhr"]["friendlyname"],
                                "image": '%s/favicon.ico' % base_url,
                                "epg": '%s/api/xmltv' % base_url,
                                "stations": []
                                }

            channel_items = []

            if origin_name:
                if channel == "all":
                    fileName = "channels.w3u"
                    for fhdhr_channel_id in self.fhdhr.origins.origins_dict[origin_name].channels.list_channel_ids:
                        channel_obj = self.fhdhr.origins.origins_dict[origin_name].channels.find_channel_obj(fhdhr_channel_id, searchkey="id")
                        if channel_obj:
                            if channel_obj.enabled:
                                channel_items.append(channel_obj)
                elif str(channel) in [str(x) for x in self.fhdhr.origins.origins_dict[origin_name].channels.create_channel_list("number")]:
                    channel_obj = self.fhdhr.origins.origins_dict[origin_name].channels.find_channel_obj(channel, searchkey="number")
                    if channel_obj:
                        fileName = "%s.w3u" % channel_obj.number
                        if channel_obj.enabled:
                            channel_items.append(channel_obj)
                        else:
                            return "Channel Disabled"
                elif channel != "all" and str(channel) in [str(x) for x in self.fhdhr.origins.origins_dict[origin_name].channels.create_channel_list("id")]:
                    channel_obj = self.fhdhr.origins.origins_dict[origin_name].channels.find_channel_obj(channel, searchkey="id")
                    if channel_obj:
                        fileName = "%s.w3u" % channel_obj.number
                        if channel_obj.enabled:
                            channel_items.append(channel_obj)
                        else:
                            return "Channel Disabled"
            elif not origin_name and channel == "all":
                fileName = "channels.w3u"
                for origin_name in self.fhdhr.origins.list_origins:
                    for fhdhr_channel_id in self.fhdhr.origins.origins_dict[origin_name].channels.list_channel_ids:
                        channel_obj = self.fhdhr.origins.origins_dict[origin_name].channels.find_channel_obj(fhdhr_channel_id, searchkey="id")
                        if channel_obj:
                            if channel_obj.enabled:
                                channel_items.append(channel_obj)
            elif not origin_name and channel != "all" and str(channel) in [str(x) for x in self.fhdhr.origins.get_channel_list("id")]:
                channel_obj = self.fhdhr.origins.find_channel_obj(channel, searchkey="id", origin_name=None)
                if channel_obj:
                    fileName = "%s.w3u" % channel_obj.number
                    if channel_obj.enabled:
                        channel_items.append(channel_obj)
                    else:
                        return "Channel Disabled"
            else:
                return "Invalid Channel"

            if not len(channel_items):
                return "Invalid Channel"

            channels_info = {}

            for channel_obj in channel_items:

                if self.fhdhr.config.dict["epg"]["images"] == "proxy" or not channel_obj.thumbnail:
                    logourl = ('%s/api/images?method=get&type=channel&id=%s' %
                               (base_url, str(channel_obj.dict['origin_id'])))
                else:
                    logourl = channel_obj.thumbnail

                channels_info[channel_obj.number] = {
                                                    "name": str(channel_obj.dict['name']),
                                                    "url": "%s%s" % (base_url, channel_obj.api_stream_url),
                                                    "epgId": str(channel_obj.dict['origin_id']),
                                                    "image": logourl,
                                                    }

            # Sort the channels
            sorted_channel_list = channel_sort(list(channels_info.keys()))
            for channel in sorted_channel_list:
                channel_info_w3u["stations"].append(channels_info[channel])

            channels_info_json = json.dumps(channel_info_w3u, indent=4)

            resp = Response(status=200, response=channels_info_json, mimetype='application/json')
            resp.headers["content-disposition"] = "attachment; filename=%s" % fileName
            return resp

            return Response(status=200,
                            response=channels_info_json,
                            mimetype='application/json')

        if redirect_url:
            if "?" in redirect_url:
                return redirect("%s&retmessage=%s" % (redirect_url, urllib.parse.quote("%s Success" % method)))
            else:
                return redirect("%s?retmessage=%s" % (redirect_url, urllib.parse.quote("%s Success" % method)))
        else:
            return "%s Success" % method
