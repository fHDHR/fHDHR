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

            FORMAT_DESCRIPTOR = "#EXTM3U"
            RECORD_MARKER = "#EXTINF"

            fakefile = StringIO()

            xmltvurl = ('%s/api/xmltv' % base_url)

            fakefile.write(
                            "%s\n" % (
                                     FORMAT_DESCRIPTOR + " " +
                                     "url-tvg=\"" + xmltvurl + "\"" + " " +
                                     "x-tvg-url=\"" + xmltvurl + "\"")
                            )

            channel_items = []

            if channel == "all":
                fileName = "channels.m3u"
                for fhdhr_id in [x["id"] for x in self.fhdhr.device.channels.get_channels()]:
                    channel_obj = self.fhdhr.device.channels.list[fhdhr_id]
                    if channel_obj.enabled:
                        channel_items.append(channel_obj)
            elif str(channel) in [str(x) for x in self.fhdhr.device.channels.get_channel_list("number")]:
                channel_obj = self.fhdhr.device.channels.get_channel_obj("number", channel)
                fileName = str(channel_obj.number) + ".m3u"
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
                                                    "group-title": self.fhdhr.config.dict["fhdhr"]["friendlyname"],
                                                    "group-titleb": str(channel_obj.dict['name']),
                                                    "stream_url": "%s%s" % (base_url, channel_obj.stream_url)
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
            resp.headers["content-disposition"] = "attachment; filename=" + fileName
            return resp

        if redirect_url:
            return redirect(redirect_url + "?retmessage=" + urllib.parse.quote("%s Success" % method))
        else:
            return "%s Success" % method
