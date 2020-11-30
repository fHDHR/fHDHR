

from .direct_stream import Direct_Stream
from .direct_m3u8_stream import Direct_M3U8_Stream
from .ffmpeg_stream import FFMPEG_Stream
from .vlc_stream import VLC_Stream


class Stream():

    def __init__(self, fhdhr, stream_args, tuner):
        self.fhdhr = fhdhr
        self.stream_args = stream_args

        if stream_args["method"] == "ffmpeg":
            self.method = FFMPEG_Stream(fhdhr, stream_args, tuner)
        if stream_args["method"] == "vlc":
            self.method = VLC_Stream(fhdhr, stream_args, tuner)
        elif (stream_args["method"] == "direct" and
              not self.stream_args["true_content_type"].startswith(tuple(["application/", "text/"]))):
            self.method = Direct_Stream(fhdhr, stream_args, tuner)
        elif (stream_args["method"] == "direct" and
              self.stream_args["true_content_type"].startswith(tuple(["application/", "text/"]))):
            self.method = Direct_M3U8_Stream(fhdhr, stream_args, tuner)

    def get(self):
        return self.method.get()
