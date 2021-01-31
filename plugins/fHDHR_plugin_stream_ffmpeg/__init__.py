import os
import sys
import subprocess

from fHDHR.exceptions import TunerError


def setup(plugin):

    # Check config for ffmpeg path
    ffmpeg_path = None
    if plugin.config.dict["ffmpeg"]["path"]:
        # verify path is valid
        if os.path.isfile(plugin.config.dict["ffmpeg"]["path"]):
            ffmpeg_path = plugin.config.dict["ffmpeg"]["path"]
        else:
            plugin.logger.warning("Failed to find ffmpeg at %s." % plugin.config.dict["ffmpeg"]["path"])

    if not ffmpeg_path:
        plugin.logger.info("Attempting to find ffmpeg in PATH.")
        if plugin.config.internal["versions"]["Operating System"]["version"] in ["Linux", "Darwin"]:
            find_ffmpeg_command = ["which", "ffmpeg"]
        elif plugin.config.internal["versions"]["Operating System"]["version"] in ["Windows"]:
            find_ffmpeg_command = ["where", "ffmpeg"]

        ffmpeg_proc = subprocess.Popen(find_ffmpeg_command, stdout=subprocess.PIPE)
        ffmpeg_path = ffmpeg_proc.stdout.read().decode().strip("\n")
        ffmpeg_proc.terminate()
        ffmpeg_proc.communicate()
        ffmpeg_proc.kill()
        if not ffmpeg_path:
            ffmpeg_path = None
        elif ffmpeg_path.isspace():
            ffmpeg_path = None

        if ffmpeg_path:
            plugin.config.dict["ffmpeg"]["path"] = ffmpeg_path

    if ffmpeg_path:
        ffmpeg_command = [ffmpeg_path, "-version", "pipe:stdout"]
        try:
            ffmpeg_proc = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE)
            ffmpeg_version = ffmpeg_proc.stdout.read().decode().split("version ")[1].split(" ")[0]
        except FileNotFoundError:
            ffmpeg_version = None
        except PermissionError:
            ffmpeg_version = None
        finally:
            ffmpeg_proc.terminate()
            ffmpeg_proc.communicate()
            ffmpeg_proc.kill()

    if not ffmpeg_version:
        ffmpeg_version = "Missing"
        plugin.logger.warning("Failed to find ffmpeg.")

    plugin.config.register_version("ffmpeg", ffmpeg_version, "env")


class Plugin_OBJ():

    def __init__(self, fhdhr, plugin_utils, stream_args, tuner):
        self.fhdhr = fhdhr
        self.plugin_utils = plugin_utils
        self.stream_args = stream_args
        self.tuner = tuner

        if self.plugin_utils.config.internal["versions"]["ffmpeg"] == "Missing":
            raise TunerError("806 - Tune Failed: FFMPEG Missing")

        self.bytes_per_read = int(plugin_utils.config.dict["streaming"]["bytes_per_read"])
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
                self.plugin_utils.logger.info("Connection Closed: Tuner Lock Removed")

            except GeneratorExit:
                self.plugin_utils.logger.info("Connection Closed.")
            except Exception as e:
                self.plugin_utils.logger.info("Connection Closed: %s" % e)
            finally:
                ffmpeg_proc.terminate()
                ffmpeg_proc.communicate()
                ffmpeg_proc.kill()
                self.plugin_utils.logger.info("Connection Closed: Tuner Lock Removed")
                if hasattr(self.fhdhr.origins.origins_dict[self.tuner.origin], "close_stream"):
                    self.fhdhr.origins.origins_dict[self.tuner.origin].close_stream(self.tuner.number, self.stream_args)
                self.tuner.close()
                # raise TunerError("806 - Tune Failed")

        return generate()

    def ffmpeg_command_assemble(self, stream_args):
        ffmpeg_command = [
                          self.plugin_utils.config.dict["ffmpeg"]["path"],
                          "-i", stream_args["stream_info"]["url"],
                          ]
        ffmpeg_command.extend(self.ffmpeg_headers(stream_args))
        ffmpeg_command.extend(self.ffmpeg_duration(stream_args))
        ffmpeg_command.extend(self.transcode_profiles(stream_args))
        ffmpeg_command.extend(self.ffmpeg_loglevel())
        ffmpeg_command.extend(["pipe:stdout"])
        return ffmpeg_command

    def ffmpeg_headers(self, stream_args):
        ffmpeg_command = []
        if stream_args["stream_info"]["headers"]:
            headers_string = ""
            if len(list(stream_args["stream_info"]["headers"].keys())) > 1:
                for x in list(stream_args["stream_info"]["headers"].keys()):
                    headers_string += "%s: %s\r\n" % (x, stream_args["stream_info"]["headers"][x])
            else:
                for x in list(stream_args["stream_info"]["headers"].keys()):
                    headers_string += "%s: %s" % (x, stream_args["stream_info"]["headers"][x])
            ffmpeg_command.extend(["-headers", '\"%s\"' % headers_string])
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
        log_level = self.plugin_utils.config.dict["logging"]["level"].lower()

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

        if stream_args["transcode_quality"]:
            self.plugin_utils.logger.info("Client requested a %s transcode for stream." % stream_args["transcode_quality"])

        ffmpeg_command = []

        if not stream_args["transcode_quality"] or stream_args["transcode_quality"] == "heavy":
            ffmpeg_command.extend([
                                    "-c", "copy",
                                    "-f", "mpegts"
                                    ])

        elif stream_args["transcode_quality"] == "mobile":
            ffmpeg_command.extend([
                                    "-c", "copy",
                                    "-s", "1280X720",
                                    "-b:v", "500k",
                                    "-b:a", "128k",
                                    "-f", "mpegts"
                                    ])

        elif stream_args["transcode_quality"] == "internet720":
            ffmpeg_command.extend([
                                    "-c", "copy",
                                    "-s", "1280X720",
                                    "-b:v", "1000k",
                                    "-b:a", "196k",
                                    "-f", "mpegts"
                                    ])

        elif stream_args["transcode_quality"] == "internet480":
            ffmpeg_command.extend([
                                    "-c", "copy",
                                    "-s", "848X480",
                                    "-b:v", "400k",
                                    "-b:a", "128k",
                                    "-f", "mpegts"
                                    ])

        elif stream_args["transcode_quality"] == "internet360":
            ffmpeg_command.extend([
                                    "-c", "copy",
                                    "-s", "640X360",
                                    "-b:v", "250k",
                                    "-b:a", "96k",
                                    "-f", "mpegts"
                                    ])

        elif stream_args["transcode_quality"] == "internet240":
            ffmpeg_command.extend([
                                    "-c", "copy",
                                    "-s", "432X240",
                                    "-b:v", "250k",
                                    "-b:a", "96k",
                                    "-f", "mpegts"
                                    ])

        return ffmpeg_command
