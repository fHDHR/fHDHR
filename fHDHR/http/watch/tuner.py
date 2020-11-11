from flask import Response, request, stream_with_context, abort


class Tuner():
    endpoints = ['/tuner<tuner>/<channel>']
    endpoint_name = "tuner"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, tuner, channel, *args):
        return self.get(tuner, channel, *args)

    def get(self, tuner, channel, *args):

        if channel.startswith("v"):
            channel_number = channel.replace('v', '')
        elif channel.startswith("ch"):
            channel_freq = channel.replace('ch', '').split("-")[0]
            subchannel = 0
            if "-" in channel:
                subchannel = channel.replace('ch', '').split("-")[1]
            abort(503, "Not Implemented %s-%s" % (str(channel_freq), str(subchannel)))

        if channel_number not in list(self.fhdhr.device.channels.list.keys()):
            abort(404, "Not Found")

        base_url = request.url_root[:-1]
        stream_args = {
                        "channel": channel_number,
                        "method": request.args.get('method', default=self.fhdhr.config.dict["fhdhr"]["stream_type"], type=str),
                        "duration": request.args.get('duration', default=0, type=int),
                        "transcode": request.args.get('transcode', default=None, type=int),
                        "accessed": self.fhdhr.device.channels.get_fhdhr_stream_url(base_url, channel_number),
                        "tuner": tuner
                        }
        stream_args = self.fhdhr.device.watch.get_stream_info(stream_args)

        if not stream_args["channelUri"]:
            abort(503, "Service Unavailable")

        if stream_args["channelUri"]:
            if stream_args["method"] == "direct":
                return Response(self.fhdhr.device.watch.get_stream(stream_args), content_type=stream_args["content_type"], direct_passthrough=True)
            elif stream_args["method"] == "ffmpeg":
                return Response(stream_with_context(self.fhdhr.device.watch.get_stream(stream_args)), mimetype="video/mpeg")
