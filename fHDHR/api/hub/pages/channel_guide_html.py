from io import StringIO
import datetime

from fHDHR.tools import humanized_time


class Channel_Guide_HTML():

    def __init__(self, settings, device, page_elements):
        self.config = settings
        self.device = device
        self.page_elements = page_elements

    def get_channel_guide_html(self, force_update=False):

        friendlyname = self.config.dict["fhdhr"]["friendlyname"]

        nowtime = datetime.datetime.utcnow()

        fakefile = StringIO()

        for line in self.page_elements["top"]:
            fakefile.write(line + "\n")

        fakefile.write("<h4 id=\"mcetoc_1cdobsl3g0\" style=\"text-align: center;\"><span style=\"text-decoration: underline;\"><strong><em>What's On %s</em></strong></span></h4>\n" % friendlyname)
        fakefile.write("\n")

        fakefile.write("<table style=\"width:100%\">\n")
        fakefile.write("  <tr>\n")
        fakefile.write("    <th>Play</th>\n")
        fakefile.write("    <th>Channel Name</th>\n")
        fakefile.write("    <th>Channel Number</th>\n")
        fakefile.write("    <th>Channel Thumbnail</th>\n")
        fakefile.write("    <th>Content Title</th>\n")
        fakefile.write("    <th>Content Thumbnail</th>\n")
        fakefile.write("    <th>Content Description</th>\n")
        fakefile.write("    <th>Content Remaining Time</th>\n")
        fakefile.write("  </tr>\n")

        for channel in self.device.epg.whats_on_allchans():
            end_time = datetime.datetime.strptime(channel["listing"][0]["time_end"], '%Y%m%d%H%M%S +0000')
            remaining_time = humanized_time(int((end_time - nowtime).total_seconds()))
            play_url = ("/%s.m3u\n" % (channel["number"]))

            fakefile.write("  <tr>\n")
            fakefile.write("    <td><a href=\"%s\">%s</a>\n" % (play_url, "Play"))
            fakefile.write("    <td>%s</td>\n" % (channel["name"]))
            fakefile.write("    <td>%s</td>\n" % (channel["number"]))
            fakefile.write("    <td><img src=\"%s\" alt=\"%s\" width=\"100\" height=\"100\">\n" % (channel["thumbnail"], channel["name"]))
            fakefile.write("    <td>%s</td>\n" % (channel["listing"][0]["title"]))
            fakefile.write("    <td><img src=\"%s\" alt=\"%s\" width=\"100\" height=\"100\">\n" % (channel["listing"][0]["thumbnail"], channel["listing"][0]["title"]))
            fakefile.write("    <td>%s</td>\n" % (channel["listing"][0]["description"]))
            fakefile.write("    <td>%s</td>\n" % (str(remaining_time)))
            fakefile.write("  </tr>\n")

        for line in self.page_elements["end"]:
            fakefile.write(line + "\n")

        channel_guide_html = fakefile.getvalue()

        return channel_guide_html
