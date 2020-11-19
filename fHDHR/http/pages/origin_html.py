from flask import request, render_template


class Origin_HTML():
    endpoints = ["/origin", "/origin.html"]
    endpoint_name = "origin"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        origin_status_dict = self.fhdhr.device.channels.get_origin_status()
        origin_status_dict["Total Channels"] = str(self.fhdhr.device.channels.get_station_total())
        return render_template('origin.html', request=request, fhdhr=self.fhdhr, origin_status_dict=origin_status_dict, list=list)
