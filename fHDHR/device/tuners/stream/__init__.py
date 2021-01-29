

from .direct_stream import Direct_Stream
from .direct_m3u8_stream import Direct_M3U8_Stream


class Stream():

    def __init__(self, fhdhr, stream_args, tuner):
        self.fhdhr = fhdhr
        self.stream_args = stream_args

        if stream_args["method"] == "direct":
            if self.stream_args["true_content_type"].startswith(tuple(["application/", "text/"])):
                self.method = Direct_M3U8_Stream(fhdhr, stream_args, tuner)
            else:
                self.method = Direct_Stream(fhdhr, stream_args, tuner)
        else:
            plugin_name = self.fhdhr.config.dict["streaming"]["valid_methods"][stream_args["method"]]["plugin"]
            self.method = self.fhdhr.plugins.plugins[plugin_name].Plugin_OBJ(self.fhdhr.plugins.plugins[plugin_name].plugin_utils, stream_args, tuner)

    def get(self):
        return self.method.get()
