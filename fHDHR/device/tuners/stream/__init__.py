

from .direct_stream import Direct_Stream
from .direct_m3u8_stream import Direct_M3U8_Stream


class Stream():

    def __init__(self, fhdhr, stream_args, tuner, plugins):
        self.fhdhr = fhdhr
        self.stream_args = stream_args

        self.plugins = plugins

        if stream_args["method"] == "direct":
            if self.stream_args["true_content_type"].startswith(tuple(["application/", "text/"])):
                self.method = Direct_M3U8_Stream(fhdhr, stream_args, tuner)
            else:
                self.method = Direct_Stream(fhdhr, stream_args, tuner)
        else:

            self.method = eval("self.plugins.%s_Stream(fhdhr, stream_args, tuner)" % stream_args["method"].upper())

    def get(self):
        return self.method.get()
