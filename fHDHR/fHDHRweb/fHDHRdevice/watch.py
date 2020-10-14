import subprocess
import time

from fHDHR.fHDHRerrors import TunerError
import fHDHR.tools


class WatchStream():

    def __init__(self, settings, origserv, tuners):
        self.config = settings
        self.origserv = origserv
        self.tuners = tuners
        self.web = fHDHR.tools.WebReq()

    def direct_stream(self, stream_args, tunernum):

        chunksize = int(self.tuners.config.dict["direct_stream"]['chunksize'])

        if not stream_args["duration"] == 0:
            stream_args["duration"] += time.time()

        req = self.web.session.get(stream_args["channelUri"], stream=True)

        def generate():
            try:
                for chunk in req.iter_content(chunk_size=chunksize):

                    if not stream_args["duration"] == 0 and not time.time() < stream_args["duration"]:
                        req.close()
                        print("Requested Duration Expired.")
                        break

                    yield chunk

            except GeneratorExit:
                req.close()
                print("Connection Closed.")
                self.tuners.tuner_close(tunernum)

        return generate()

    def ffmpeg_stream(self, stream_args, tunernum):

        bytes_per_read = int(self.config.dict["ffmpeg"]["bytes_per_read"])

        ffmpeg_command = [self.config.dict["ffmpeg"]["ffmpeg_path"],
                          "-i", stream_args["channelUri"],
                          "-c", "copy",
                          "-f", "mpegts",
                          "-nostats", "-hide_banner",
                          "-loglevel", "fatal",
                          "pipe:stdout"
                          ]

        if not stream_args["duration"] == 0:
            stream_args["duration"] += time.time()

        ffmpeg_proc = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE)

        def generate():
            try:
                while True:

                    if not stream_args["duration"] == 0 and not time.time() < stream_args["duration"]:
                        ffmpeg_proc.terminate()
                        ffmpeg_proc.communicate()
                        print("Requested Duration Expired.")
                        break

                    videoData = ffmpeg_proc.stdout.read(bytes_per_read)
                    if not videoData:
                        break

                    try:
                        yield videoData

                    except Exception as e:
                        ffmpeg_proc.terminate()
                        ffmpeg_proc.communicate()
                        print("Connection Closed: " + str(e))

            except GeneratorExit:
                ffmpeg_proc.terminate()
                ffmpeg_proc.communicate()
                print("Connection Closed.")
                self.tuners.tuner_close(tunernum)

        return generate()

    def get_stream(self, stream_args):

        try:
            tunernum = self.tuners.tuner_grab(stream_args)
        except TunerError as e:
            print("A " + stream_args["method"] + " stream request for channel " +
                  str(stream_args["channel"]) + " was rejected do to " + str(e))
            return

        print("Attempting a " + stream_args["method"] + " stream request for channel " + str(stream_args["channel"]))

        if stream_args["method"] == "ffmpeg":
            return self.ffmpeg_stream(stream_args, tunernum)
        elif stream_args["method"] == "direct":
            return self.direct_stream(stream_args, tunernum)

    def get_stream_info(self, stream_args):

        stream_args["channelUri"] = self.origserv.get_channel_stream(str(stream_args["channel"]))
        if not stream_args["channelUri"]:
            print("Could not Obtain Channel Stream.")
            stream_args["content_type"] = "video/mpeg"
        else:
            channelUri_headers = self.web.session.head(stream_args["channelUri"]).headers
            stream_args["content_type"] = channelUri_headers['Content-Type']

        return stream_args
