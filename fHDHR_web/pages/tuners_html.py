from flask import request, render_template, session

from fHDHR.tools import humanized_filesize


class Tuners_HTML():
    endpoints = ["/tuners", "/tuners.html"]
    endpoint_name = "page_streams_html"
    endpoint_access_level = 0
    pretty_name = "Tuners"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        tuner_list = []
        tuner_status = self.fhdhr.device.tuners.status()
        tuner_scanning = 0
        for tuner in list(tuner_status.keys()):
            tuner_dict = {
                          "number": str(tuner),
                          "status": str(tuner_status[tuner]["status"]),
                          }
            if tuner_status[tuner]["status"] == "Active":
                tuner_dict["channel_number"] = tuner_status[tuner]["channel"]
                tuner_dict["method"] = tuner_status[tuner]["method"]
                tuner_dict["play_duration"] = str(tuner_status[tuner]["Play Time"])
                tuner_dict["downloaded"] = humanized_filesize(tuner_status[tuner]["downloaded"])
            elif tuner_status[tuner]["status"] == "Scanning":
                tuner_scanning += 1

            tuner_list.append(tuner_dict)

        return render_template('tuners.html', session=session, request=request, fhdhr=self.fhdhr, tuner_list=tuner_list, tuner_scanning=tuner_scanning)
