from io import StringIO


class Diagnostics_HTML():

    def __init__(self, settings, device, page_elements):
        self.config = settings
        self.device = device
        self.diagnostics_html = None
        self.page_elements = page_elements

    def get_diagnostics_html(self, base_url, force_update=False):
        if not self.diagnostics_html or force_update:

            fakefile = StringIO()
            page_elements = self.page_elements.get()

            for line in page_elements["top"]:
                fakefile.write(line + "\n")

            # a list of 2 part lists containing button information
            button_list = [
                            ["Force Channel Update", "chanscan"],
                            ["debug", "debug.json"],
                            ["device.xml", "device.xml"],
                            ["discover.json", "discover.json"],
                            ["lineup.json", "lineup.json"],
                            ["lineup_status.json", "lineup_status.json"],
                            ["cluster.json", "cluster.json"]
                            ]

            for button_item in button_list:
                button_label = button_item[0]
                button_path = button_item[1]
                fakefile.write("<div style=\"text-align: center;\">\n")
                fakefile.write("  <p><button onclick=\"OpenLink('%s')\">%s</a></button></p>\n" % (button_path, button_label))
                fakefile.write("</div>\n")
            fakefile.write("\n")

            for line in page_elements["end"]:
                fakefile.write(line + "\n")

            self.diagnostics_html = fakefile.getvalue()

        return self.diagnostics_html
