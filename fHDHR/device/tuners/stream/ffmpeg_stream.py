import sys
import subprocess

# from fHDHR.exceptions import TunerError


class FFMPEG_Stream():

    def __init__(self, fhdhr, stream_args, tuner):
        self.fhdhr = fhdhr
        self.stream_args = stream_args
        self.tuner = tuner

        self.bytes_per_read = int(self.fhdhr.config.dict["streaming"]["bytes_per_read"])
        self.ffmpeg_command = self.ffmpeg_command_assemble(stream_args)

    def get(self):

        ffmpeg_proc = subprocess.Popen(self.ffmpeg_command, stdout=subprocess.PIPE)

        def generate():
            try:
                while self.tuner.tuner_lock.locked():

                    chunk = ffmpeg_proc.stdout.read(self.bytes_per_read)
                    if not chunk:
                        break
                        # raise TunerError("807 - No Video Data")
                    yield chunk
                    chunk_size = int(sys.getsizeof(chunk))
                    self.tuner.add_downloaded_size(chunk_size)
                self.fhdhr.logger.info("Connection Closed: Tuner Lock Removed")

            except GeneratorExit:
                self.fhdhr.logger.info("Connection Closed.")
            except Exception as e:
                self.fhdhr.logger.info("Connection Closed: " + str(e))
            finally:
                ffmpeg_proc.terminate()
                ffmpeg_proc.communicate()
                ffmpeg_proc.kill()
                self.fhdhr.logger.info("Connection Closed: Tuner Lock Removed")
                self.tuner.close()
                # raise TunerError("806 - Tune Failed")

        return generate()

    def ffmpeg_command_assemble(self, stream_args):
        ffmpeg_command = [
                          self.fhdhr.config.dict["ffmpeg"]["path"],
                          "-i", stream_args["stream_info"]["url"],
                          ]
        ffmpeg_command.extend(self.ffmpeg_duration(stream_args))
        ffmpeg_command.extend(self.transcode_profiles(stream_args))
        ffmpeg_command.extend(self.ffmpeg_loglevel())
        ffmpeg_command.extend(["pipe:stdout"])
        return ffmpeg_command

    def ffmpeg_duration(self, stream_args):
        ffmpeg_command = []
        if stream_args["duration"]:
            ffmpeg_command.extend(["-t", str(stream_args["duration"])])
        else:
            ffmpeg_command.extend(
                                  [
                                   "-reconnect", "1",
                                   "-reconnect_at_eof", "1",
                                   "-reconnect_streamed", "1",
                                   "-reconnect_delay_max", "2",
                                  ]
                                  )

        return ffmpeg_command

    def ffmpeg_loglevel(self):
        ffmpeg_command = []
        log_level = self.fhdhr.config.dict["logging"]["level"].lower()

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
        return ffmpeg_command

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
            stream_args["transcode"] = None

        ffmpeg_command = []

        if not stream_args["transcode"]:
            ffmpeg_command.extend(
                                    [
                                     "-c", "copy",
                                     "-f", "mpegts",
                                    ]
                                    )
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

        return ffmpeg_command
