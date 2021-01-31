import os
import sys
import subprocess

from fHDHR.exceptions import TunerError


def setup(plugin):

    # Check config for vlc path
    vlc_path = None
    if plugin.config.dict["vlc"]["path"]:
        # verify path is valid
        if os.path.isfile(plugin.config.dict["vlc"]["path"]):
            vlc_path = plugin.config.dict["vlc"]["path"]
        else:
            plugin.logger.warning("Failed to find vlc at %s." % plugin.config.dict["vlc"]["path"])

    if not vlc_path:
        plugin.logger.info("Attempting to find vlc in PATH.")
        if plugin.config.internal["versions"]["Operating System"]["version"] in ["Linux", "Darwin"]:
            find_vlc_command = ["which", "vlc"]
        elif plugin.config.internal["versions"]["Operating System"]["version"] in ["Windows"]:
            find_vlc_command = ["where", "vlc"]

        vlc_proc = subprocess.Popen(find_vlc_command, stdout=subprocess.PIPE)
        vlc_path = vlc_proc.stdout.read().decode().strip("\n")
        vlc_proc.terminate()
        vlc_proc.communicate()
        vlc_proc.kill()
        if not vlc_path:
            vlc_path = None
        elif vlc_path.isspace():
            vlc_path = None

        if vlc_path:
            plugin.config.dict["vlc"]["path"] = vlc_path

    if vlc_path:
        vlc_command = [vlc_path, "--version", "pipe:stdout"]
        try:
            vlc_proc = subprocess.Popen(vlc_command, stdout=subprocess.PIPE)
            vlc_version = vlc_proc.stdout.read().decode().split("version ")[1].split('\n')[0]
        except FileNotFoundError:
            vlc_version = None
        except PermissionError:
            vlc_version = None
        finally:
            vlc_proc.terminate()
            vlc_proc.communicate()
            vlc_proc.kill()

    if not vlc_version:
        vlc_version = "Missing"
        plugin.logger.warning("Failed to find vlc.")

    plugin.config.register_version("vlc", vlc_version, "env")


class Plugin_OBJ():

    def __init__(self, fhdhr, plugin_utils, stream_args, tuner):
        self.fhdhr = fhdhr
        self.plugin_utils = plugin_utils
        self.stream_args = stream_args
        self.tuner = tuner

        if self.plugin_utils.config.internal["versions"]["vlc"]["version"] == "Missing":
            raise TunerError("806 - Tune Failed: VLC Missing")

        self.bytes_per_read = int(self.plugin_utils.config.dict["streaming"]["bytes_per_read"])
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
                self.plugin_utils.logger.info("Connection Closed: Tuner Lock Removed")

            except GeneratorExit:
                self.plugin_utils.logger.info("Connection Closed.")
            except Exception as e:
                self.plugin_utils.logger.info("Connection Closed: %s" % e)
            finally:
                vlc_proc.terminate()
                vlc_proc.communicate()
                vlc_proc.kill()
                self.plugin_utils.logger.info("Connection Closed: Tuner Lock Removed")
                if hasattr(self.fhdhr.origins.origins_dict[self.tuner.origin], "close_stream"):
                    self.fhdhr.origins.origins_dict[self.tuner.origin].close_stream(self.tuner.number, self.stream_args)
                self.tuner.close()
                # raise TunerError("806 - Tune Failed")

        return generate()

    def vlc_command_assemble(self, stream_args):
        vlc_command = [
                          self.plugin_utils.config.dict["vlc"]["path"],
                          "-I", "dummy", stream_args["stream_info"]["url"],
                          ]
        # vlc_command.extend(self.vlc_headers(stream_args))
        vlc_command.extend(self.vlc_duration(stream_args))
        vlc_command.extend(self.vlc_loglevel())
        vlc_command.extend(["--sout"])
        vlc_command.extend(self.transcode_profiles(stream_args))
        return vlc_command

    def vlc_headers(self, stream_args):
        vlc_command = []
        return vlc_command

    def vlc_duration(self, stream_args):
        vlc_command = []
        if stream_args["duration"]:
            vlc_command.extend(["--run-time=%s" % str(stream_args["duration"])])
        return vlc_command

    def vlc_loglevel(self):
        vlc_command = []
        log_level = self.plugin_utils.config.dict["logging"]["level"].lower()

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
        vlc_command = []

        if stream_args["transcode_quality"]:
            self.plugin_utils.logger.info("Client requested a %s transcode for stream." % stream_args["transcode_quality"])

        transcode_dict = {}
        if not stream_args["transcode_quality"] or stream_args["transcode_quality"] == "heavy":
            # dummy do nothing line
            vlc_command.extend([])

        elif stream_args["transcode_quality"] == "mobile":
            transcode_dict["transcode"] = {
                                           "width": "1280",
                                           "height": "720",
                                           "vb": "500",
                                           "ab": "128"
                                           }

        elif stream_args["transcode_quality"] == "internet720":
            transcode_dict["transcode"] = {
                                           "width": "1280",
                                           "height": "720",
                                           "vb": "1000",
                                           "ab": "196"
                                           }

        elif stream_args["transcode_quality"] == "internet480":
            transcode_dict["transcode"] = {
                                           "width": "848",
                                           "height": "480",
                                           "vb": "400",
                                           "ab": "128"
                                           }

        elif stream_args["transcode_quality"] == "internet360":
            transcode_dict["transcode"] = {
                                           "width": "640",
                                           "height": "360",
                                           "vb": "250",
                                           "ab": "96"
                                           }

        elif stream_args["transcode_quality"] == "internet240":
            transcode_dict["transcode"] = {
                                           "width": "432",
                                           "height": "240",
                                           "vb": "250",
                                           "ab": "96"
                                           }

        transcode_dict["std"] = {
                                   "mux": "ts",
                                   "access": "file",
                                   "dst": "-"
                                   }

        topkey_index = 0
        vlc_transcode_string = ""
        for topkey in list(transcode_dict.keys()):
            if not topkey_index:
                topkey_index += 1
                vlc_transcode_string += "#"
            else:
                vlc_transcode_string += ":"
            vlc_transcode_string += "%s{" % topkey
            vlc_transcode_string += ",".join(["%s=%s" % (x, transcode_dict[topkey][x]) for x in list(transcode_dict[topkey].keys())])
            vlc_transcode_string += "}"
        vlc_command.extend([vlc_transcode_string])

        return vlc_command
