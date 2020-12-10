from flask import request, render_template_string
import pathlib
from io import StringIO
import datetime

from fHDHR.tools import humanized_time


class Origin_HTML():
    endpoints = ["/origin", "/origin.html"]
    endpoint_name = "page_origin_html"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

        self.template_file = pathlib.Path(self.fhdhr.config.internal["paths"]["origin_web"]).joinpath('origin.html')
        self.template = StringIO()
        self.template.write(open(self.template_file).read())

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        if self.fhdhr.originwrapper.setup_success:
            donation_expire = humanized_time(
               int((self.fhdhr.originwrapper.originservice.status_dict["donateExp"] -
                    datetime.datetime.utcnow()).total_seconds()))
            origin_status_dict = {
                                    "Login": "Success",
                                    "Username": self.fhdhr.config.dict["origin"]["username"],
                                    "DMA": self.fhdhr.originwrapper.originservice.location["DMA"],
                                    "City": self.fhdhr.originwrapper.originservice.location["city"],
                                    "Latitude": self.fhdhr.originwrapper.originservice.location["latitude"],
                                    "Longitude": self.fhdhr.originwrapper.originservice.location["longitude"],
                                    "Donation Expiration": donation_expire,
                                    "Total Channels": len(self.fhdhr.device.channels.list)
                                    }
        else:
            origin_status_dict = {"Setup": "Failed"}
        return render_template_string(self.template.getvalue(), request=request, fhdhr=self.fhdhr, origin_status_dict=origin_status_dict, list=list)
