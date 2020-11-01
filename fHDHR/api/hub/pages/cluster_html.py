from io import StringIO
import urllib.parse
import requests


class Cluster_HTML():

    def __init__(self, settings, device, page_elements):
        self.config = settings
        self.device = device
        self.page_elements = page_elements

    def get_cluster_html(self, base_url, force_update=False):

        fakefile = StringIO()

        page_elements = self.page_elements.get()

        for line in page_elements["top"]:
            fakefile.write(line + "\n")

        fakefile.write("<h4 style=\"text-align: center;\">Cluster</h4>")
        fakefile.write("\n")

        fakefile.write("<div style=\"text-align: center;\">\n")
        fakefile.write("  <button onclick=\"OpenLink('%s')\">%s</a></button>\n" % ("/cluster?method=scan", "Force Scan"))
        fakefile.write("  <button onclick=\"OpenLink('%s')\">%s</a></button>\n" % ("/cluster?method=disconnect", "Disconnect"))
        fakefile.write("</div><br>\n")

        fakefile.write("<table class=\"center\" style=\"width:50%\">\n")
        fakefile.write("  <tr>\n")
        fakefile.write("    <th>Name</th>\n")
        fakefile.write("    <th>Location</th>\n")
        fakefile.write("    <th>Joined</th>\n")
        fakefile.write("    <th>Options</th>\n")
        fakefile.write("  </tr>\n")

        fhdhr_list = self.device.cluster.get_list()
        for location in list(fhdhr_list.keys()):
            fakefile.write("  <tr>\n")

            if location in list(self.device.cluster.cluster.keys()):
                location_name = self.device.cluster.cluster[location]["name"]
            else:
                try:
                    location_info_url = location + "/discover.json"
                    locatation_info_req = requests.get(location_info_url)
                    location_info = locatation_info_req.json()
                    location_name = location_info["FriendlyName"]
                except requests.exceptions.ConnectionError:
                    print("Unreachable: " + location)
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
                    ("/cluster?method=add&location=" + location_url_query, "Add"))
            else:
                fakefile.write(
                    "  <button onclick=\"OpenLink('%s')\">%s</a></button>\n" %
                    ("/cluster?method=del&location=" + location_url_query, "Remove"))
            fakefile.write("        </div>\n")
            fakefile.write("    </td>\n")

            fakefile.write("  </tr>\n")

        for line in page_elements["end"]:
            fakefile.write(line + "\n")

        return fakefile.getvalue()
