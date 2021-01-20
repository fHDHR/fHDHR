from flask import request, abort, redirect
import urllib.parse


class Tuner():
    endpoints = ['/tuner<tuner_number>/<channel>', '/hdhr/tuner<tuner_number>/<channel>']
    endpoint_name = "hdhr_tuner"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, tuner_number, channel, *args):
        return self.get(tuner_number, channel, *args)

    def get(self, tuner_number, channel, *args):

        method = request.args.get('method', default=self.fhdhr.config.dict["streaming"]["method"], type=str)

        redirect_url = "/api/tuners?method=%s" % (method)

        redirect_url += "&tuner=%s" % str(tuner_number)

        if channel.startswith("v"):
            channel_number = channel.replace('v', '')
        elif channel.startswith("ch"):
            channel_freq = channel.replace('ch', '').split("-")[0]
            subchannel = 0
            if "-" in channel:
                subchannel = channel.replace('ch', '').split("-")[1]
            self.fhdhr.logger.error("Not Implemented %s-%s" % (str(channel_freq), str(subchannel)))
            abort(501, "Not Implemented %s-%s" % (str(channel_freq), str(subchannel)))
        else:
            channel_number = channel

        redirect_url += "&channel=%s" % str(channel_number)

        duration = request.args.get('duration', default=0, type=int)
        if duration:
            redirect_url += "&duration=%s" % str(duration)

        transcode_quality = request.args.get('transcode', default=None, type=str)
        if transcode_quality:
            redirect_url += "&transcode=%s" % str(transcode_quality)

        redirect_url += "&accessed=%s" % urllib.parse.quote(request.url)

        return redirect(redirect_url)
