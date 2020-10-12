from io import StringIO


class channels_M3U():

    def __init__(self, settings, origserv):
        self.config = settings
        self.origserv = origserv

    def get_channels_m3u(self, base_url):

        FORMAT_DESCRIPTOR = "#EXTM3U"
        RECORD_MARKER = "#EXTINF"

        fakefile = StringIO()

        xmltvurl = ('%s%s/xmltv.xml' %
                    ("http://",
                     base_url))

        fakefile.write(
                        "%s\n" % (
                                 FORMAT_DESCRIPTOR + " " +
                                 "url-tvg=\"" + xmltvurl + "\"" + " " +
                                 "x-tvg-url=\"" + xmltvurl + "\"")
                        )

        for channel in self.origserv.get_channels():

            logourl = ('%s%s/images?source=epg&type=channel&id=%s' %
                       ("http://",
                        base_url,
                        str(channel['id'])))

            fakefile.write(
                            "%s\n" % (
                                      RECORD_MARKER + ":0" + " " +
                                      "channelID=\"" + str(channel['id']) + "\" " +
                                      "tvg-chno=\"" + str(channel['number']) + "\" " +
                                      "tvg-name=\"" + str(channel['name']) + "\" " +
                                      "tvg-id=\"" + str(channel['number']) + "\" " +
                                      "tvg-logo=\"" + logourl + "\" " +
                                      "group-title=\"" + self.config.dict["fhdhr"]["friendlyname"] + "," + str(channel['name']))
                            )

            fakefile.write(
                            "%s\n" % (
                                        ('%s%s/watch?method=%s&channel=%s' %
                                         ("http://",
                                          base_url,
                                          self.config.dict["fhdhr"]["stream_type"],
                                          str(channel['number'])))
                             )
                            )

        return fakefile.getvalue()
