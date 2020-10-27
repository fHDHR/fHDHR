from io import StringIO


class Origin_HTML():

    def __init__(self, settings, device, page_elements):
        self.config = settings
        self.device = device
        self.page_elements = page_elements

    def get_origin_html(self, base_url, force_update=False):

        servicename = str(self.config.dict["main"]["servicename"])

        fakefile = StringIO()

        for line in self.page_elements["top"]:
            fakefile.write(line + "\n")

        fakefile.write("<h4 style=\"text-align: center;\">%s Status</h4>" % (servicename))
        fakefile.write("\n")

        fakefile.write("<table class=\"center\" style=\"width:50%\">\n")
        fakefile.write("  <tr>\n")
        fakefile.write("    <th></th>\n")
        fakefile.write("    <th></th>\n")
        fakefile.write("  </tr>\n")

        origin_status_dict = self.device.channels.get_origin_status()
        for key in list(origin_status_dict.keys()):
            fakefile.write("  <tr>\n")
            fakefile.write("    <td>%s</td>\n" % (str(key)))
            fakefile.write("    <td>%s</td>\n" % (str(origin_status_dict[key])))
            fakefile.write("  </tr>\n")

        for line in self.page_elements["end"]:
            fakefile.write(line + "\n")

        return fakefile.getvalue()
