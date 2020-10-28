from io import StringIO


class Index_HTML():

    def __init__(self, settings, device, page_elements):
        self.config = settings
        self.device = device
        self.page_elements = page_elements

    def get_index_html(self, base_url, force_update=False):

        fakefile = StringIO()

        for line in self.page_elements["top"]:
            fakefile.write(line + "\n")

        fakefile.write("<h4 style=\"text-align: center;\">fHDHR Status</h4>")
        fakefile.write("\n")

        fakefile.write("<table class=\"center\" style=\"width:50%\">\n")
        fakefile.write("  <tr>\n")
        fakefile.write("    <th></th>\n")
        fakefile.write("    <th></th>\n")
        fakefile.write("  </tr>\n")

        total_channels = self.device.channels.get_station_total()

        tuners_in_use = self.device.tuners.inuse_tuner_count()
        max_tuners = self.device.tuners.max_tuners

        tableguts = [
                    ["Script Directory", str(self.config.dict["filedir"]["script_dir"])],
                    ["Config File", str(self.config.config_file)],
                    ["Cache Path", str(self.config.dict["filedir"]["cache_dir"])],
                    ["Total Channels", str(total_channels)],
                    ["Tuner Usage", "%s/%s" % (str(tuners_in_use), str(max_tuners))]
                    ]

        for guts in tableguts:
            fakefile.write("  <tr>\n")
            fakefile.write("    <td>%s</td>\n" % (guts[0]))
            fakefile.write("    <td>%s</td>\n" % (guts[1]))
            fakefile.write("  </tr>\n")

        for line in self.page_elements["end"]:
            fakefile.write(line + "\n")

        return fakefile.getvalue()
