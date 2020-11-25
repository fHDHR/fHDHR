from flask import request, render_template


class Streams_HTML():
    endpoints = ["/streams", "/streams.html"]
    endpoint_name = "page_streams_html"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        tuner_list = []
        tuner_status = self.fhdhr.device.tuners.status()
        for tuner in list(tuner_status.keys()):
            tuner_dict = {
                          "number": str(tuner),
                          "status": str(tuner_status[tuner]["status"]),
                          }
            if tuner_status[tuner]["status"] == "Active":
                tuner_dict["channel_number"] = tuner_status[tuner]["channel"]
                tuner_dict["method"] = tuner_status[tuner]["method"]
                tuner_dict["play_duration"] = str(tuner_status[tuner]["Play Time"])

            tuner_list.append(tuner_dict)

        return render_template('streams.html', request=request, fhdhr=self.fhdhr, tuner_list=tuner_list)
