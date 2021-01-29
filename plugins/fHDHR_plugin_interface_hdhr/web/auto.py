from flask import request, abort, redirect
import urllib.parse


class Auto():
    endpoints = ['/hdhr/auto/<channel>']
    endpoint_name = "hdhr_auto"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    @property
    def source(self):
        return self.fhdhr.config.dict["hdhr"]["source"] or self.fhdhr.origins.valid_origins[0]

    def __call__(self, channel, *args):
        return self.get(channel, *args)

    def get(self, channel, *args):

        origin = self.source

        redirect_url = "/api/tuners?method=%s" % (self.fhdhr.config.dict["streaming"]["method"])

        if channel.startswith("v"):
            channel_number = channel.replace('v', '')
        elif channel.startswith("ch"):
            channel_freq = channel.replace('ch', '').split("-")[0]
            subchannel = None
            if "-" in channel:
                subchannel = channel.replace('ch', '').split("-")[1]
            if subchannel:
                self.fhdhr.logger.error("Not Implemented %s-%s" % (channel_freq, subchannel))
                abort(501, "Not Implemented %s-%s" % (channel_freq, subchannel))
            else:
                self.fhdhr.logger.error("Not Implemented %s" % (channel_freq, subchannel))
                abort(501, "Not Implemented %s" % channel_freq)
        else:
            channel_number = channel

        redirect_url += "&channel=%s" % str(channel_number)
        redirect_url += "&origin=%s" % str(origin)

        duration = request.args.get('duration', default=0, type=int)
        if duration:
            redirect_url += "&duration=%s" % str(duration)

        transcode_quality = request.args.get('transcode', default=None, type=str)
        if transcode_quality:
            redirect_url += "&transcode=%s" % str(transcode_quality)

        redirect_url += "&accessed=%s" % urllib.parse.quote(request.url)

        return redirect(redirect_url)
