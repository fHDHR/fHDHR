import os

from fHDHR.exceptions import TunerError

# TODO Needs more work, testing


class Direct_FILE_Stream():
    """
    A method to stream from /dev/ hardware devices directly.
    """

    def __init__(self, fhdhr, stream_args, tuner):
        self.fhdhr = fhdhr
        self.stream_args = stream_args
        self.tuner = tuner

        if not os.path.isfile(self.stream_args["stream_info"]["url"]):
            raise TunerError("806 - Tune Failed: %s PATH does not seem to exist" % self.stream_args["stream_info"]["url"])

    def get(self):
        """
        Produce chunks of video data.
        """

        self.fhdhr.logger.info("Direct Hardware Stream from file: %s" % (self.stream_args["stream_info"]["url"]))

        def generate():

            chunk_counter = 0

            try:
                while self.tuner.tuner_lock.locked():

                    with open(self.stream_args["stream_info"]["url"], 'r') as device_stream:

                        chunk_counter += 1
                        self.fhdhr.logger.debug("Reading Chunk #%s" % chunk_counter)

                        chunk = device_stream.read(self.stream_args["bytes_per_read"])

                        if not chunk:
                            break

                        yield chunk

            except Exception as exerror:
                error_out = self.fhdhr.logger.lazy_exception(exerror, "Chunk #%s unable to process" % chunk_counter)
                self.fhdhr.logger.error(error_out)

        return generate()
