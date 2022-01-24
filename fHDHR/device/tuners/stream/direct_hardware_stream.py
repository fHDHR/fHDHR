
from fHDHR.exceptions import TunerError

# TODO write this method


class Direct_HardWare_Stream():
    """
    A method to stream from /dev/ hardware devices directly.
    """

    def __init__(self, fhdhr, stream_args, tuner):
        self.fhdhr = fhdhr
        self.stream_args = stream_args
        self.tuner = tuner

        self.bytes_per_read = int(self.fhdhr.config.dict["streaming"]["bytes_per_read"])

        raise TunerError("806 - Tune Failed: Feature not implemented")

    def get(self):
        """
        Produce chunks of video data.
        """

        self.fhdhr.logger.info("Direct Hardware Stream from device: %s" % (self.stream_args["stream_info"]["url"]))

        def generate():

            chunk_counter = 0

            try:
                while self.tuner.tuner_lock.locked():

                    chunk_counter += 1
                    self.fhdhr.logger.debug("Downloading Chunk #%s" % chunk_counter)

                    chunk = None

                    if not chunk:
                        break

                    yield chunk

            except Exception:
                yield None

        return generate()
