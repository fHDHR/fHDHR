import os

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

        self.bytes_per_read = int(self.fhdhr.config.dict["streaming"]["bytes_per_read"])

        if not os.path.exists(self.stream_args["stream_info"]["url"]):
            raise TunerError("806 - Tune Failed: %s PATH does not seem to exist" % self.stream_args["stream_info"]["url"])

    def get(self):
        """
        Produce chunks of video data.
        """

        self.fhdhr.logger.info("Direct Hardware Stream from device: %s" % (self.stream_args["stream_info"]["url"]))

        def generate():

            chunk_counter = 0

            try:
                while self.tuner.tuner_lock.locked():

                    with open(self.stream_args["stream_info"]["url"], 'r') as device_stream:

                        chunk_counter += 1
                        self.fhdhr.logger.debug("Pulling Chunk #%s" % chunk_counter)

                        chunk = device_stream.read(self.bytes_per_read)

                        if not chunk:
                            break

                        yield chunk

            except Exception as err:
                self.fhdhr.logger.error("Chunk #%s unable to process: %s" % (chunk_counter, err))

        return generate()
