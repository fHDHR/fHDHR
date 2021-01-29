from flask import request, render_template_string, session
import pathlib
from io import StringIO
import datetime

from fHDHR.tools import humanized_time


class Locast_HTML():
    endpoints = ["/locast", "/locast.html"]
    endpoint_name = "page_locast_html"
    endpoint_category = "pages"
    pretty_name = "Locast"

    def __init__(self, fhdhr, plugin_utils):
        self.fhdhr = fhdhr
        self.plugin_utils = plugin_utils

        self.origin = plugin_utils.origin

        self.template_file = pathlib.Path(fhdhr.config.dict["plugin_web_paths"][plugin_utils.namespace]["path"]).joinpath('locast.html')
        self.template = StringIO()
        self.template.write(open(self.template_file).read())

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        if self.origin.setup_success:
            donation_expire = humanized_time(
               int((self.origin.status_dict["donateExp"] -
                    datetime.datetime.utcnow()).total_seconds()))
            origin_status_dict = {
                                    "Login": "Success",
                                    "Username": self.plugin_utils.config.dict["locast"]["username"],
                                    "DMA": self.origin.location["DMA"],
                                    "City": self.origin.location["city"],
                                    "Latitude": self.origin.location["latitude"],
                                    "Longitude": self.origin.location["longitude"],
                                    "Donation Expiration": donation_expire,
                                    "Total Channels": len(list(self.fhdhr.device.channels.list["locast"].keys()))
                                    }
        else:
            origin_status_dict = {"Setup": "Failed"}
        return render_template_string(self.template.getvalue(), request=request, session=session, fhdhr=self.fhdhr, origin_status_dict=origin_status_dict, list=list)
