from flask import request
from io import StringIO


class Index_HTML():
    endpoints = ["/", "/index.html"]
    endpoint_name = "root"

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

        fakefile.write("<h4 style=\"text-align: center;\">fHDHR Status</h4>")
        fakefile.write("\n")

        fakefile.write("<table class=\"center\" style=\"width:50%\">\n")
        fakefile.write("  <tr>\n")
        fakefile.write("    <th></th>\n")
        fakefile.write("    <th></th>\n")
        fakefile.write("  </tr>\n")

        total_channels = self.fhdhr.device.channels.get_station_total()

        tuners_in_use = self.fhdhr.device.tuners.inuse_tuner_count()
        max_tuners = self.fhdhr.device.tuners.max_tuners

        tableguts = [
                    ["Script Directory", str(self.fhdhr.config.dict["filedir"]["script_dir"])],
                    ["Config File", str(self.fhdhr.config.config_file)],
                    ["Cache Path", str(self.fhdhr.config.dict["filedir"]["cache_dir"])],
                    ["Total Channels", str(total_channels)],
                    ["Tuner Usage", "%s/%s" % (str(tuners_in_use), str(max_tuners))]
                    ]

        for guts in tableguts:
            fakefile.write("  <tr>\n")
            fakefile.write("    <td>%s</td>\n" % (guts[0]))
            fakefile.write("    <td>%s</td>\n" % (guts[1]))
            fakefile.write("  </tr>\n")

        for line in page_elements["end"]:
            fakefile.write(line + "\n")

        return fakefile.getvalue()
