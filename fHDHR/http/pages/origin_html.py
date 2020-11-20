from flask import request, render_template


class Origin_HTML():
    endpoints = ["/origin", "/origin.html"]
    endpoint_name = "origin_html"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        origin_status_dict = self.fhdhr.origin.get_status_dict()
        origin_status_dict["Total Channels"] = len(self.fhdhr.device.channels.list)
        return render_template('origin.html', request=request, fhdhr=self.fhdhr, origin_status_dict=origin_status_dict, list=list)
