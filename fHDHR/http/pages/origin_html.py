from flask import request
from io import StringIO


class Origin_HTML():
    endpoints = ["/origin", "/origin.html"]
    endpoint_name = "origin"

    def __init__(self, fhdhr, page_elements):
        self.fhdhr = fhdhr
        self.page_elements = page_elements

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        servicename = str(self.fhdhr.config.dict["main"]["servicename"])

        fakefile = StringIO()
        page_elements = self.page_elements.get(request)

        for line in page_elements["top"]:
            fakefile.write(line + "\n")

        fakefile.write("<h4 style=\"text-align: center;\">%s Status</h4>" % (servicename))
        fakefile.write("\n")

        # a list of 2 part lists containing button information
        button_list = [
                        ["Force Channel Update", "/api/channels?method=scan&redirect=%2Forigin"],
                        ]

        fakefile.write("<div style=\"text-align: center;\">\n")
        for button_item in button_list:
            button_label = button_item[0]
            button_path = button_item[1]
            fakefile.write("  <p><button onclick=\"OpenLink('%s')\">%s</a></button></p>\n" % (button_path, button_label))
        fakefile.write("</div>\n")
        fakefile.write("\n")

        fakefile.write("<table class=\"center\" style=\"width:50%\">\n")
        fakefile.write("  <tr>\n")
        fakefile.write("    <th></th>\n")
        fakefile.write("    <th></th>\n")
        fakefile.write("  </tr>\n")

        origin_status_dict = self.fhdhr.device.channels.get_origin_status()
        for key in list(origin_status_dict.keys()):
            fakefile.write("  <tr>\n")
            fakefile.write("    <td>%s</td>\n" % (str(key)))
            fakefile.write("    <td>%s</td>\n" % (str(origin_status_dict[key])))
            fakefile.write("  </tr>\n")

        total_channels = self.fhdhr.device.channels.get_station_total()
        fakefile.write("  <tr>\n")
        fakefile.write("    <td>%s</td>\n" % ("Total Channels"))
        fakefile.write("    <td>%s</td>\n" % (str(total_channels)))
        fakefile.write("  </tr>\n")

        for line in page_elements["end"]:
            fakefile.write(line + "\n")

        return fakefile.getvalue()
