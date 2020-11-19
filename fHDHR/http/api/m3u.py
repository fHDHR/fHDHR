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

            channel_list = self.fhdhr.device.channels.get_channels()
            channel_number_list = [x["number"] for x in channel_list]

            if channel == "all":
                channel_items = channel_list
            elif channel in channel_number_list:
                channel_items = [self.fhdhr.device.channels.get_channel_dict("number", channel)]
            else:
                return "Invalid Channel"

            for channel_item in channel_items:

                logourl = ('%s/api/images?method=get&type=channel&id=%s' %
                           (base_url, str(channel_item['id'])))

                fakefile.write(
                                "%s\n" % (
                                          RECORD_MARKER + ":0" + " " +
                                          "channelID=\"" + str(channel_item['id']) + "\" " +
                                          "tvg-chno=\"" + str(channel_item['number']) + "\" " +
                                          "tvg-name=\"" + str(channel_item['name']) + "\" " +
                                          "tvg-id=\"" + str(channel_item['number']) + "\" " +
                                          "tvg-logo=\"" + logourl + "\" " +
                                          "group-title=\"" + self.fhdhr.config.dict["fhdhr"]["friendlyname"] + "\"," + str(channel_item['name']))
                                )

                fakefile.write(
                                "%s\n" % (
                                            ('%s/auto/v%s' %
                                             (base_url, str(channel_item['number'])))
                                 )
                                )

                channels_m3u = fakefile.getvalue()

            return Response(status=200,
                            response=channels_m3u,
                            mimetype='audio/x-mpegurl')

        if redirect_url:
            return redirect(redirect_url + "?retmessage=" + urllib.parse.quote("%s Success" % method))
        else:
            return "%s Success" % method
