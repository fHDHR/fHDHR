import sys
import subprocess

# from fHDHR.exceptions import TunerError


class VLC_Stream():

    def __init__(self, fhdhr, stream_args, tuner):
        self.fhdhr = fhdhr
        self.stream_args = stream_args
        self.tuner = tuner

        self.bytes_per_read = int(self.fhdhr.config.dict["streaming"]["bytes_per_read"])
        self.vlc_command = self.vlc_command_assemble(stream_args)

    def get(self):

        vlc_proc = subprocess.Popen(self.vlc_command, stdout=subprocess.PIPE)

        def generate():
            try:

                while self.tuner.tuner_lock.locked():

                    chunk = vlc_proc.stdout.read(self.bytes_per_read)
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
                vlc_proc.terminate()
                vlc_proc.communicate()
                vlc_proc.kill()
                self.fhdhr.logger.info("Connection Closed: Tuner Lock Removed")
                self.tuner.close()
                # raise TunerError("806 - Tune Failed")

        return generate()

    def vlc_command_assemble(self, stream_args):
        vlc_command = [
                          self.fhdhr.config.dict["vlc"]["path"],
                          "-I", "dummy", stream_args["stream_info"]["url"],
                          ]
        vlc_command.extend(self.vlc_duration(stream_args))
        vlc_command.extend(self.vlc_loglevel())
        vlc_command.extend(["--sout"])
        vlc_command.extend(self.transcode_profiles(stream_args))
        return vlc_command

    def vlc_duration(self, stream_args):
        vlc_command = []
        if stream_args["duration"]:
            vlc_command.extend(["--run-time=%s" % str(stream_args["duration"])])
        return vlc_command

    def vlc_loglevel(self):
        vlc_command = []
        log_level = self.fhdhr.config.dict["logging"]["level"].lower()

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
        return vlc_command

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
        vlc_command = []

        if stream_args["transcode"]:
            self.fhdhr.logger.info("Client requested a " + stream_args["transcode"] + " transcode for stream.")
            stream_args["transcode"] = None

        vlc_transcode_string = "#std{mux=ts,access=file,dst=-}"
        return [vlc_transcode_string]

        '#transcode{vcodec=mp2v,vb=4096,acodec=mp2a,ab=192,scale=1,channels=2,deinterlace}:std{access=file,mux=ts,dst=-"}'

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

        return vlc_command
