

class Direct_Stream():
    """
    A method to stream in chunks.
    """

    def __init__(self, fhdhr, stream_args, tuner):
        self.fhdhr = fhdhr
        self.stream_args = stream_args
        self.tuner = tuner

        self.bytes_per_read = int(self.fhdhr.config.dict["streaming"]["bytes_per_read"])

    def get(self):
        """
        Produce chunks of video data.
        """

        self.fhdhr.logger.info("Direct Stream of %s URL: %s" % (self.stream_args["true_content_type"], self.stream_args["stream_info"]["url"]))

        if self.stream_args["transcode_quality"]:
            self.fhdhr.logger.info("Client requested a %s transcode for stream. Direct Method cannot transcode." % self.stream_args["transcode_quality"])

        if self.stream_args["stream_info"]["headers"]:
            req = self.fhdhr.web.session.get(self.stream_args["stream_info"]["url"], stream=True, headers=self.stream_args["stream_info"]["headers"])
        else:
            req = self.fhdhr.web.session.get(self.stream_args["stream_info"]["url"], stream=True)

        def generate():

            chunk_counter = 0

            try:

                while self.tuner.tuner_lock.locked():

                    for chunk in req.iter_content(chunk_size=self.bytes_per_read):
                        chunk_counter += 1
                        self.fhdhr.logger.debug("Downloading Chunk #%s" % chunk_counter)

                        if not chunk:
                            break

                        yield chunk

            finally:
                req.close()

        return generate()
