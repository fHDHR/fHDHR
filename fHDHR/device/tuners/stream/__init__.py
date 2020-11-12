

from .direct_stream import Direct_Stream
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
        elif stream_args["method"] == "direct":
            self.method = Direct_Stream(fhdhr, stream_args, tuner)

    def get(self):
        return self.method.get()
