from flask import Response, request, redirect
import urllib.parse
from io import StringIO

from fHDHR.tools import channel_sort


class M3U():
    endpoints = ["/api/m3u", "/api/channels.m3u"]
    endpoint_name = "api_m3u"
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

            FORMAT_DESCRIPTOR = "#EXTM3U"
            RECORD_MARKER = "#EXTINF"

            fakefile = StringIO()

            xmltvurl = ('%s/api/xmltv?source=%s' % (base_url, origin_name))

            fakefile.write("%s url-tvg=\"%s\" x-tvg-url=\"%s\"\n" % (FORMAT_DESCRIPTOR, xmltvurl, xmltvurl))

            channel_items = []

            if origin_name:
                if channel == "all":
                    fileName = "channels.m3u"
                    for fhdhr_channel_id in self.fhdhr.origins.origins_dict[origin_name].channels.list_channel_ids:
                        channel_obj = self.fhdhr.origins.origins_dict[origin_name].channels.find_channel_obj(fhdhr_channel_id, searchkey="id")
                        if channel_obj:
                            if channel_obj.enabled:
                                channel_items.append(channel_obj)
                elif str(channel) in [str(x) for x in self.fhdhr.origins.origins_dict[origin_name].channels.create_channel_list("number")]:
                    channel_obj = self.fhdhr.origins.origins_dict[origin_name].channels.find_channel_obj(channel, searchkey="number")
                    if channel_obj:
                        fileName = "%s.m3u" % channel_obj.number
                        if channel_obj.enabled:
                            channel_items.append(channel_obj)
                        else:
                            return "Channel Disabled"
                elif channel != "all" and str(channel) in [str(x) for x in self.fhdhr.origins.origins_dict[origin_name].channels.create_channel_list("id")]:
                    channel_obj = self.fhdhr.origins.origins_dict[origin_name].channels.find_channel_obj(channel, searchkey="id")
                    if channel_obj:
                        fileName = "%s.m3u" % channel_obj.number
                        if channel_obj.enabled:
                            channel_items.append(channel_obj)
                        else:
                            return "Channel Disabled"
            elif not origin_name and channel == "all":
                fileName = "channels.m3u"
                for origin_name in self.fhdhr.origins.list_origins:
                    for fhdhr_channel_id in self.fhdhr.origins.origins_dict[origin_name].channels.list_channel_ids:
                        channel_obj = self.fhdhr.origins.origins_dict[origin_name].channels.find_channel_obj(fhdhr_channel_id, searchkey="id")
                        if channel_obj:
                            if channel_obj.enabled:
                                channel_items.append(channel_obj)
            elif not origin_name and channel != "all" and str(channel) in [str(x) for x in self.fhdhr.origins.get_channel_list("id")]:
                channel_obj = self.fhdhr.origins.channels.find_channel_obj(channel, searchkey="id", origin_name=None)
                if channel_obj:
                    fileName = "%s.m3u" % channel_obj.number
                    if channel_obj.enabled:
                        channel_items.append(channel_obj)
                    else:
                        return "Channel Disabled"
            else:
                return "Invalid Channel"

            if not len(channel_items):
                return "Invalid Channel"

            stream_method = request.args.get('stream_method', default=None, type=str)
            if stream_method and stream_method not in self.fhdhr.streammanager.streaming_methods:
                return "Invalid stream_method"

            channels_info = {}
            for channel_obj in channel_items:

                if self.fhdhr.config.dict["epg"]["images"] == "proxy" or not channel_obj.thumbnail:
                    logourl = ('%s/api/images?method=get&type=channel&id=%s' %
                               (base_url, str(channel_obj.dict['origin_id'])))
                else:
                    logourl = channel_obj.thumbnail

                channels_info[channel_obj.number] = {
                                                    "channelID": str(channel_obj.dict['origin_id']),
                                                    "tvg-chno": str(channel_obj.number),
                                                    "tvg-name": str(channel_obj.dict['name']),
                                                    "tvg-id": str(channel_obj.number),
                                                    "tvg-logo": logourl,
                                                    "group-title": channel_obj.origin_name,
                                                    "group-titleb": str(channel_obj.dict['name']),
                                                    "stream_url": "%s%s" % (base_url, channel_obj.api_stream_url)
                                                    }

                if stream_method:
                    channels_info[channel_obj.number]["stream_url"] += "&stream_method=%s" % stream_method

            # Sort the channels
            sorted_channel_list = channel_sort(list(channels_info.keys()))
            sorted_chan_guide = []
            for channel in sorted_channel_list:
                sorted_chan_guide.append(channels_info[channel])

            for channel_item_dict in sorted_chan_guide:
                m3ustring = "%s:0 " % (RECORD_MARKER)
                for chan_key in list(channel_item_dict.keys()):
                    if not chan_key.startswith(tuple(["group-title", "stream_url"])):
                        m3ustring += "%s=\"%s\" " % (chan_key, channel_item_dict[chan_key])
                m3ustring += "group-title=\"%s\",%s\n" % (channel_item_dict["group-title"], channel_item_dict["group-titleb"])
                m3ustring += "%s\n" % channel_item_dict["stream_url"]
                fakefile.write(m3ustring)

            channels_m3u = fakefile.getvalue()

            resp = Response(status=200, response=channels_m3u, mimetype='audio/x-mpegurl')
            resp.headers["content-disposition"] = "attachment; filename=%s" % fileName
            return resp

        if redirect_url:
            if "?" in redirect_url:
                return redirect("%s&retmessage=%s" % (redirect_url, urllib.parse.quote("%s Success" % method)))
            else:
                return redirect("%s?retmessage=%s" % (redirect_url, urllib.parse.quote("%s Success" % method)))
        else:
            return "%s Success" % method
