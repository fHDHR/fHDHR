import os
import subprocess

from fHDHR.exceptions import TunerError

# TODO Needs more work, testing


class Direct_HardWare_Stream():
    """
    A method to stream from /dev/ hardware devices directly.
    """

    def __init__(self, fhdhr, stream_args, tuner):
        self.fhdhr = fhdhr
        self.stream_args = stream_args
        self.tuner = tuner

        if not os.path.exists(self.stream_args["stream_info"]["url"]):
            raise TunerError("806 - Tune Failed: %s PATH does not seem to exist" % self.stream_args["stream_info"]["url"])

    def get(self):
        """
        Produce chunks of video data.
        """

        self.fhdhr.logger.info("Direct Hardware Stream from device: %s" % (self.stream_args["stream_info"]["url"]))
        opersystem = self.fhdhr.versions.dict["Operating System"]["version"]
        if opersystem in ["Linux", "Darwin"]:
            self.directstr_commmand = 'cat %s' % self.stream_args["stream_info"]["url"]
        elif opersystem in ["Windows"]:
            self.directstr_commmand = 'type %s' % self.stream_args["stream_info"]["url"]
        else:
            self.fhdhr.logger.error("Operating System not recognized: %s" % opersystem)

        self.fhdhr.logger.debug("Operating System is: %s" % opersystem)
        self.fhdhr.logger.debug("Command is: %s" % self.directstr_commmand)
        directstr_proc = subprocess.Popen(self.directstr_commmand.split(' '), stdout=subprocess.PIPE)

        def generate():
            chunk_counter = 0
            try:
                while self.tuner.tuner_lock.locked():
                    chunk = directstr_proc.stdout.read(self.stream_args["bytes_per_read"])
                    chunk_counter += 1
                    self.fhdhr.logger.debug("Pulling Chunk #%s" % chunk_counter)
                    if not chunk:
                        break
                    yield chunk

            except Exception as exerror:
                error_out = self.fhdhr.logger.lazy_exception(exerror, "Chunk #%s unable to process" % chunk_counter)
                self.fhdhr.logger.error(error_out)

            finally:
                directstr_proc.terminate()
                directstr_proc.communicate()
                directstr_proc.kill()

        return generate()
