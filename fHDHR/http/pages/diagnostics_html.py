from flask import request
from io import StringIO


class Diagnostics_HTML():
    endpoints = ["/diagnostics", "/diagnostics.html"]
    endpoint_name = "diagnostics"

    def __init__(self, fhdhr, page_elements):
        self.fhdhr = fhdhr
        self.diagnostics_html = None
        self.page_elements = page_elements

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        fakefile = StringIO()
        page_elements = self.page_elements.get(request)

        for line in page_elements["top"]:
            fakefile.write(line + "\n")

        # a list of 2 part lists containing button information
        button_list = [
                        ["debug.json", "/api/debug"],
                        ["device.xml", "device.xml"],
                        ["discover.json", "discover.json"],
                        ["lineup.json", "lineup.json"],
                        ["lineup.xml", "lineup.xml"],
                        ["lineup_status.json", "lineup_status.json"],
                        ["cluster.json", "/api/cluster?method=get"]
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

        return fakefile.getvalue()
