import subprocess
import time

from fHDHR.exceptions import TunerError


class WatchStream():

    def __init__(self, fhdhr, origserv, tuners):
        self.fhdhr = fhdhr

        self.origserv = origserv
        self.tuners = tuners

    def direct_stream(self, stream_args, tunernum):

        chunksize = int(self.fhdhr.config.dict["direct_stream"]['chunksize'])

        if not stream_args["duration"] == 0:
            stream_args["duration"] += time.time()

        req = self.fhdhr.web.session.get(stream_args["channelUri"], stream=True)

        def generate():
            try:
                for chunk in req.iter_content(chunk_size=chunksize):

                    if not stream_args["duration"] == 0 and not time.time() < stream_args["duration"]:
                        req.close()
                        self.fhdhr.logger.info("Requested Duration Expired.")
                        break

                    yield chunk

            except GeneratorExit:
                req.close()
                self.fhdhr.logger.info("Connection Closed.")
                self.tuners.tuner_close(tunernum)

        return generate()

    def ffmpeg_stream(self, stream_args, tunernum):

        bytes_per_read = int(self.fhdhr.config.dict["ffmpeg"]["bytes_per_read"])

        ffmpeg_command = self.transcode_profiles(stream_args)

        if not stream_args["duration"] == 0:
            stream_args["duration"] += time.time()

        ffmpeg_proc = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE)

        def generate():
            try:
                while True:

                    if not stream_args["duration"] == 0 and not time.time() < stream_args["duration"]:
                        ffmpeg_proc.terminate()
                        ffmpeg_proc.communicate()
                        self.fhdhr.logger.info("Requested Duration Expired.")
                        break

                    videoData = ffmpeg_proc.stdout.read(bytes_per_read)
                    if not videoData:
                        break
                    yield videoData

            except GeneratorExit:
                ffmpeg_proc.terminate()
                ffmpeg_proc.communicate()
                self.fhdhr.logger.info("Connection Closed.")
                self.tuners.tuner_close(tunernum)
            except Exception as e:
                ffmpeg_proc.terminate()
                ffmpeg_proc.communicate()
                self.fhdhr.logger.info("Connection Closed: " + str(e))
                self.tuners.tuner_close(tunernum)

        return generate()

    def vlc_stream(self, stream_args, tunernum):

        bytes_per_read = int(self.fhdhr.config.dict["vlc"]["bytes_per_read"])

        vlc_command = self.transcode_profiles(stream_args)

        if not stream_args["duration"] == 0:
            stream_args["duration"] += time.time()

        vlc_proc = subprocess.Popen(vlc_command, stdout=subprocess.PIPE)

        def generate():
            try:
                while True:

                    if not stream_args["duration"] == 0 and not time.time() < stream_args["duration"]:
                        vlc_proc.terminate()
                        vlc_proc.communicate()
                        self.fhdhr.logger.info("Requested Duration Expired.")
                        break

                    videoData = vlc_proc.stdout.read(bytes_per_read)
                    if not videoData:
                        break
                    yield videoData

            except GeneratorExit:
                vlc_proc.terminate()
                vlc_proc.communicate()
                self.fhdhr.logger.info("Connection Closed.")
                self.tuners.tuner_close(tunernum)
            except Exception as e:
                vlc_proc.terminate()
                vlc_proc.communicate()
                self.fhdhr.logger.info("Connection Closed: " + str(e))
                self.tuners.tuner_close(tunernum)

        return generate()

    def get_stream(self, stream_args):

        try:
            tunernum = self.tuners.tuner_grab(stream_args)
        except TunerError as e:
            self.fhdhr.logger.info("A " + stream_args["method"] + " stream request for channel " +
                                   str(stream_args["channel"]) + " was rejected do to " + str(e))
            return

        self.fhdhr.logger.info("Attempting a " + stream_args["method"] + " stream request for channel " + str(stream_args["channel"]))

        if stream_args["method"] == "ffmpeg":
            return self.ffmpeg_stream(stream_args, tunernum)
        if stream_args["method"] == "vlc":
            return self.vlc_stream(stream_args, tunernum)
        elif stream_args["method"] == "direct":
            return self.direct_stream(stream_args, tunernum)

    def get_stream_info(self, stream_args):

        stream_args["channelUri"] = self.origserv.get_channel_stream(str(stream_args["channel"]))
        if not stream_args["channelUri"]:
            self.fhdhr.logger.error("Could not Obtain Channel Stream.")
            stream_args["content_type"] = "video/mpeg"
        else:
            channelUri_headers = self.fhdhr.web.session.head(stream_args["channelUri"]).headers
            stream_args["content_type"] = channelUri_headers['Content-Type']

        return stream_args

    def transcode_profiles(self, stream_args):
        # TODO implement actual profiles here
        """
        • heavy: transcode to AVC with the same resolution, frame-rate, and interlacing as the
        original stream. For example 1080i60 AVC 1080i60, 720p60 AVC 720p60. → →
        • mobile: trancode to AVC progressive not exceeding 1280x720 30fps.
        • internet720: transcode to low bitrate AVC progressive not exceeding 1280x720 30fps.
        • internet480: transcode to low bitrate AVC progressive not exceeding 848x480 30fps for
        16:9 content, not exceeding 640x480 30fps for 4:3 content.
        • internet360: transcode to low bitrate AVC progressive not exceeding 640x360 30fps for
        16:9 content, not exceeding 480x360 30fps for 4:3 content.
        • internet240: transcode to low bitrate AVC progressive not exceeding 432x240 30fps for
        16:9 content, not exceeding 320x240 30fps for 4:3 content
        """

        if stream_args["transcode"]:
            self.fhdhr.logger.info("Client requested a " + stream_args["transcode"] + " transcode for stream.")

        log_level = self.fhdhr.config.dict["logging"]["level"].lower()

        if stream_args["method"] == "direct":
            return None

        elif stream_args["method"] == "ffmpeg":
            ffmpeg_command = [
                              self.fhdhr.config.dict["ffmpeg"]["ffmpeg_path"],
                              "-i", stream_args["channelUri"],
                              "-c", "copy",
                              "-f", "mpegts",
                              ]

            if not stream_args["transcode"]:
                ffmpeg_command.extend([])
            elif stream_args["transcode"] == "heavy":
                ffmpeg_command.extend([])
            elif stream_args["transcode"] == "mobile":
                ffmpeg_command.extend([])
            elif stream_args["transcode"] == "internet720":
                ffmpeg_command.extend([])
            elif stream_args["transcode"] == "internet480":
                ffmpeg_command.extend([])
            elif stream_args["transcode"] == "internet360":
                ffmpeg_command.extend([])
            elif stream_args["transcode"] == "internet240":
                ffmpeg_command.extend([])

            loglevel_dict = {
                            "debug": "debug",
                            "info": "info",
                            "error": "error",
                            "warning": "warning",
                            "critical": "fatal",
                            }
            if log_level not in ["info", "debug"]:
                ffmpeg_command.extend(["-nostats", "-hide_banner"])
            ffmpeg_command.extend(["-loglevel", loglevel_dict[log_level]])

            ffmpeg_command.extend(["pipe:stdout"])
            return ffmpeg_command

        elif stream_args["method"] == "vlc":
            vlc_command = [
                            self.fhdhr.config.dict["vlc"]["vlc_path"],
                            "-I", "dummy", stream_args["channelUri"],
                            ]

            loglevel_dict = {
                            "debug": "3",
                            "info": "0",
                            "error": "1",
                            "warning": "2",
                            "critical": "1",
                            }
            vlc_command.extend(["--log-verbose=", loglevel_dict[log_level]])
            if log_level not in ["info", "debug"]:
                vlc_command.extend(["--quiet"])

            if not stream_args["transcode"]:
                vlc_command.extend([])
            elif stream_args["transcode"] == "heavy":
                vlc_command.extend([])
            elif stream_args["transcode"] == "mobile":
                vlc_command.extend([])
            elif stream_args["transcode"] == "internet720":
                vlc_command.extend([])
            elif stream_args["transcode"] == "internet480":
                vlc_command.extend([])
            elif stream_args["transcode"] == "internet360":
                vlc_command.extend([])
            elif stream_args["transcode"] == "internet240":
                vlc_command.extend([])

            vlc_command.extend(["--sout", "#std{mux=ts,access=file,dst=-}"])

            return vlc_command
