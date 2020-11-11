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
        fakefile.write("  </tr>\n")

        tuner_status = self.fhdhr.device.tuners.status()
        for tuner in list(tuner_status.keys()):
            print(tuner_status[tuner])
        for tuner in list(tuner_status.keys()):
            fakefile.write("  <tr>\n")
            fakefile.write("    <td>%s</td>\n" % (str(tuner)))
            fakefile.write("    <td>%s</td>\n" % (str(tuner_status[tuner]["status"])))
            if tuner_status[tuner]["status"] == "Active":
                fakefile.write("    <td>%s<img src=\"%s\" alt=\"%s\" width=\"100\" height=\"100\">%s</td>\n" % (
                    tuner_status[tuner]["epg"]["name"], tuner_status[tuner]["epg"]["thumbnail"], tuner_status[tuner]["epg"]["name"], str(tuner_status[tuner]["epg"]["number"])))
                fakefile.write("    <td>%s</td>\n" % (str(tuner_status[tuner]["method"])))
                fakefile.write("    <td>%s</td>\n" % (str(tuner_status[tuner]["Play Time"])))
            else:
                fakefile.write("    <td>%s</td>\n" % "N/A")
                fakefile.write("    <td>%s</td>\n" % "N/A")
                fakefile.write("    <td>%s</td>\n" % "N/A")
            fakefile.write("  </tr>\n")

        for line in page_elements["end"]:
            fakefile.write(line + "\n")

        return fakefile.getvalue()
