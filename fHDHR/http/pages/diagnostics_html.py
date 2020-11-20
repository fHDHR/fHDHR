from flask import request, render_template


class Diagnostics_HTML():
    endpoints = ["/diagnostics", "/diagnostics.html"]
    endpoint_name = "diagnostics_html"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

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

        return render_template('diagnostics.html', request=request, fhdhr=self.fhdhr, button_list=button_list)
