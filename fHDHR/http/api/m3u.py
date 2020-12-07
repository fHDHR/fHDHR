from flask import Response, request, redirect
import urllib.parse
from io import StringIO


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
                for fhdhr_id in list(self.fhdhr.device.channels.list.keys()):
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

            for channel_obj in channel_items:

                if self.fhdhr.config.dict["epg"]["images"] == "proxy" or not channel_obj.thumbnail:
                    logourl = ('%s/api/images?method=get&type=channel&id=%s' %
                               (base_url, str(channel_obj.dict['origin_id'])))
                else:
                    logourl = channel_obj.thumbnail

                fakefile.write(
                                "%s\n" % (
                                          RECORD_MARKER + ":0" + " " +
                                          "channelID=\"" + str(channel_obj.dict['origin_id']) + "\" " +
                                          "tvg-chno=\"" + str(channel_obj.dict['number']) + "\" " +
                                          "tvg-name=\"" + str(channel_obj.dict['name']) + "\" " +
                                          "tvg-id=\"" + str(channel_obj.dict['number']) + "\" " +
                                          "tvg-logo=\"" + logourl + "\" " +
                                          "group-title=\"" + self.fhdhr.config.dict["fhdhr"]["friendlyname"] + "\"," + str(channel_obj.dict['name']))
                                )

                fakefile.write("%s%s\n" % (base_url, channel_obj.stream_url))

                channels_m3u = fakefile.getvalue()

            resp = Response(status=200, response=channels_m3u, mimetype='audio/x-mpegurl')
            resp.headers["content-disposition"] = "attachment; filename=" + fileName
            return resp

        if redirect_url:
            return redirect(redirect_url + "?retmessage=" + urllib.parse.quote("%s Success" % method))
        else:
            return "%s Success" % method
