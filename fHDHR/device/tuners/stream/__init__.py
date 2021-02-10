

from .direct_stream import Direct_Stream
from .direct_m3u8_stream import Direct_M3U8_Stream
from fHDHR.exceptions import TunerError


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
            plugin_name = self.get_alt_stream_plugin(stream_args["method"])
            if plugin_name:
                self.method = self.fhdhr.plugins.plugins[plugin_name].Plugin_OBJ(fhdhr, self.fhdhr.plugins.plugins[plugin_name].plugin_utils, stream_args, tuner)
            else:
                raise TunerError("806 - Tune Failed: Plugin Not Found")

    def get_alt_stream_plugin(self, method):
        for plugin_name in list(self.fhdhr.plugins.plugins.keys()):
            if self.fhdhr.plugins.plugins[plugin_name].type == "alt_stream":
                if self.fhdhr.plugins.plugins[plugin_name].name == method:
                    return plugin_name
        return None

    def get(self):
        return self.method.get()
