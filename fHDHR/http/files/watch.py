from flask import Response, request, stream_with_context, abort


class Watch():
    endpoints = ['/auto/<channel>']
    endpoint_name = "auto"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, channel, *args):
        return self.get(channel, *args)

    def get(self, channel, *args):

        base_url = request.url_root[:-1]
        stream_args = {
                        "channel": channel.replace('v', ''),
                        "method": request.args.get('method', default=self.fhdhr.config.dict["fhdhr"]["stream_type"], type=str),
                        "duration": request.args.get('duration', default=0, type=int),
                        "accessed": self.fhdhr.device.channels.get_fhdhr_stream_url(base_url, channel.replace('v', '')),
                        }
        stream_args = self.fhdhr.device.watch.get_stream_info(stream_args)
        if stream_args["channelUri"]:
            if stream_args["method"] == "direct":
                return Response(self.fhdhr.device.watch.get_stream(stream_args), content_type=stream_args["content_type"], direct_passthrough=True)
            elif stream_args["method"] == "ffmpeg":
                return Response(stream_with_context(self.fhdhr.device.watch.get_stream(stream_args)), mimetype="video/mpeg")
        abort(503)
