from flask import request
from io import StringIO
import urllib.parse


class Cluster_HTML():
    endpoints = ["/cluster", "/cluster.html"]
    endpoint_name = "cluster"

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

        fakefile.write("<h4 style=\"text-align: center;\">Cluster</h4>")
        fakefile.write("\n")

        if self.fhdhr.config.dict["fhdhr"]["discovery_address"]:

            fakefile.write("<div style=\"text-align: center;\">\n")
            fakefile.write("  <button onclick=\"OpenLink('%s')\">%s</a></button>\n" % ("/api/cluster?method=scan&redirect=%2Fcluster", "Force Scan"))
            fakefile.write("  <button onclick=\"OpenLink('%s')\">%s</a></button>\n" % ("/api/cluster?method=disconnect&redirect=%2Fcluster", "Disconnect"))
            fakefile.write("</div><br>\n")

            fakefile.write("<table class=\"center\" style=\"width:50%\">\n")
            fakefile.write("  <tr>\n")
            fakefile.write("    <th>Name</th>\n")
            fakefile.write("    <th>Location</th>\n")
            fakefile.write("    <th>Joined</th>\n")
            fakefile.write("    <th>Options</th>\n")
            fakefile.write("  </tr>\n")

            fhdhr_list = self.fhdhr.device.cluster.get_list()
            for location in list(fhdhr_list.keys()):
                fakefile.write("  <tr>\n")

                if location in list(self.fhdhr.device.cluster.cluster().keys()):
                    location_name = self.fhdhr.device.cluster.cluster()[location]["name"]
                else:
                    try:
                        location_info_url = location + "/discover.json"
                        locatation_info_req = self.fhdhr.web.session.get(location_info_url)
                        location_info = locatation_info_req.json()
                        location_name = location_info["FriendlyName"]
                    except self.fhdhr.web.exceptions.ConnectionError:
                        self.fhdhr.logger.error("Unreachable: " + location)
                fakefile.write("    <td>%s</td>\n" % (str(location_name)))

                fakefile.write("    <td>%s</td>\n" % (str(location)))

                fakefile.write("    <td>%s</td>\n" % (str(fhdhr_list[location]["Joined"])))

                fakefile.write("    <td>\n")
                fakefile.write("        <div>\n")
                location_url_query = urllib.parse.quote(location)
                fakefile.write(
                    "  <button onclick=\"OpenLink('%s')\">%s</a></button>\n" %
                    (location, "Visit"))
                if not fhdhr_list[location]["Joined"]:
                    fakefile.write(
                        "  <button onclick=\"OpenLink('%s')\">%s</a></button>\n" %
                        ("/api/cluster?method=add&location=" + location_url_query + "&redirect=%2Fcluster", "Add"))
                else:
                    fakefile.write(
                        "  <button onclick=\"OpenLink('%s')\">%s</a></button>\n" %
                        ("/api/cluster?method=del&location=" + location_url_query + "&redirect=%2Fcluster", "Remove"))
                fakefile.write("        </div>\n")
                fakefile.write("    </td>\n")

                fakefile.write("  </tr>\n")
        else:
            fakefile.write("<p style=\"text-align: center;\">Discovery Address must be set for SSDP/Cluster</p>\n")

        for line in page_elements["end"]:
            fakefile.write(line + "\n")

        return fakefile.getvalue()
