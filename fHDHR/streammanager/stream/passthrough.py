

class Direct_FILE_Stream():
    """
    A method to stream from /dev/ hardware devices directly.
    """

    def __init__(self, fhdhr, stream_args, tuner):
        self.fhdhr = fhdhr
        self.stream_args = stream_args
        self.tuner = tuner

    def get(self):
        """
        Produce chunks of video data.
        """

        self.fhdhr.logger.info("Passthrough Stream from device: %s" % (self.stream_args["stream_info"]["url"]))

        return None
