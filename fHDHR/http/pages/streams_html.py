from flask import request
from io import StringIO


class Streams_HTML():
    endpoints = ["/streams", "/streams.html"]
    endpoint_name = "streams"

    def __init__(self, fhdhr, page_elements):
        self.fhdhr = fhdhr
        self.page_elements = page_elements

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        fakefile = StringIO()
        page_elements = self.page_elements.get(request)

        for line in page_elements["top"]:
            fakefile.write(line + "\n")

        fakefile.write("<h4 style=\"text-align: center;\">fHDHR Streams</h4>")
        fakefile.write("\n")

        fakefile.write("<table style=\"width:100%\">\n")
        fakefile.write("  <tr>\n")
        fakefile.write("    <th>Tuner</th>\n")
        fakefile.write("    <th>Status</th>\n")
        fakefile.write("    <th>Channel</th>\n")
        fakefile.write("    <th>Method</th>\n")
        fakefile.write("    <th>Time Active</th>\n")
        fakefile.write("    <th>Options</th>\n")
        fakefile.write("  </tr>\n")

        tuner_status = self.fhdhr.device.tuners.status()
        for tuner in list(tuner_status.keys()):
            fakefile.write("  <tr>\n")
            fakefile.write("    <td>%s</td>\n" % (str(tuner)))
            fakefile.write("    <td>%s</td>\n" % (str(tuner_status[tuner]["status"])))
            if tuner_status[tuner]["status"] == "Active":
                try:
                    channel_name = tuner_status[tuner]["epg"]["name"]
                    channel_number = tuner_status[tuner]["epg"]["number"]
                    channel_thumbnail = tuner_status[tuner]["epg"]["thumbnail"]
                    fakefile.write("    <td>%s<img src=\"%s\" alt=\"%s\" width=\"100\" height=\"100\">%s</td>\n" % (
                        channel_name, channel_thumbnail, channel_name, str(channel_number)))
                except TypeError:
                    fakefile.write("    <td>%s</td>\n" % (str(tuner_status[tuner]["channel"])))
                fakefile.write("    <td>%s</td>\n" % (str(tuner_status[tuner]["method"])))
                fakefile.write("    <td>%s</td>\n" % (str(tuner_status[tuner]["Play Time"])))
            else:
                fakefile.write("    <td>%s</td>\n" % "N/A")
                fakefile.write("    <td>%s</td>\n" % "N/A")
                fakefile.write("    <td>%s</td>\n" % "N/A")

            fakefile.write("    <td>\n")
            fakefile.write("        <div>\n")

            if tuner_status[tuner]["status"] in ["Active", "Acquired"]:
                fakefile.write(
                    "  <button onclick=\"OpenLink('%s')\">%s</a></button>\n" %
                    ("/api/watch?method=close&tuner=" + str(tuner) + "&redirect=%2Fstreams", "Close"))
            fakefile.write("        </div>\n")
            fakefile.write("    </td>\n")

            fakefile.write("  </tr>\n")

        for line in page_elements["end"]:
            fakefile.write(line + "\n")

        return fakefile.getvalue()
