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
        return self.get(*args)

    def get(self, *args):

        base_url = request.url_root[:-1]

        method = request.args.get('method', default="get", type=str)
        channel = request.args.get('channel', default="all", type=str)
        redirect_url = request.args.get('redirect', default=None, type=str)

        if method == "get":

            origin_methods = self.fhdhr.origins.valid_origins
            origin = request.args.get('origin', default=None, type=str)
            if origin and origin not in origin_methods:
                return "%s Invalid channels origin" % origin

            FORMAT_DESCRIPTOR = "#EXTM3U"
            RECORD_MARKER = "#EXTINF"

            fakefile = StringIO()

            xmltvurl = ('%s/api/xmltv' % base_url)

            fakefile.write("%s url-tvg=\"%s\" x-tvg-url=\"%s\"\n" % (FORMAT_DESCRIPTOR, xmltvurl, xmltvurl))

            channel_items = []

            if origin:
                if channel == "all":
                    fileName = "channels.m3u"
                    for fhdhr_id in [x["id"] for x in self.fhdhr.device.channels.get_channels(origin)]:
                        channel_obj = self.fhdhr.device.channels.get_channel_obj("id", fhdhr_id, origin)
                        if channel_obj.enabled:
                            channel_items.append(channel_obj)
                elif str(channel) in [str(x) for x in self.fhdhr.device.channels.get_channel_list("number", origin)]:
                    channel_obj = self.fhdhr.device.channels.get_channel_obj("number", channel, origin)
                    fileName = "%s.m3u" % channel_obj.number
                    if channel_obj.enabled:
                        channel_items.append(channel_obj)
                    else:
                        return "Channel Disabled"
                elif channel != "all" and str(channel) in [str(x) for x in self.fhdhr.device.channels.get_channel_list("id", origin)]:
                    channel_obj = self.fhdhr.device.channels.get_channel_obj("id", channel, origin)
                    fileName = "%s.m3u" % channel_obj.number
                    if channel_obj.enabled:
                        channel_items.append(channel_obj)
                    else:
                        return "Channel Disabled"
            elif not origin and channel == "all":
                fileName = "channels.m3u"
                for origin in list(self.fhdhr.origins.origins_dict.keys()):
                    for fhdhr_id in [x["id"] for x in self.fhdhr.device.channels.get_channels(origin)]:
                        channel_obj = self.fhdhr.device.channels.get_channel_obj("id", fhdhr_id, origin)
                        if channel_obj.enabled:
                            channel_items.append(channel_obj)
            elif not origin and channel != "all" and str(channel) in [str(x) for x in self.fhdhr.device.channels.get_channel_list("id")]:
                channel_obj = self.fhdhr.device.channels.get_channel_obj("id", channel)
                fileName = "%s.m3u" % channel_obj.number
                if channel_obj.enabled:
                    channel_items.append(channel_obj)
                else:
                    return "Channel Disabled"
            else:
                return "Invalid Channel"

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
                                                    "group-title": channel_obj.origin,
                                                    "group-titleb": str(channel_obj.dict['name']),
                                                    "stream_url": "%s%s" % (base_url, channel_obj.api_stream_url)
                                                    }

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
            return redirect("%s?retmessage=%s" % (redirect_url, urllib.parse.quote("%s Success" % method)))
        else:
            return "%s Success" % method
