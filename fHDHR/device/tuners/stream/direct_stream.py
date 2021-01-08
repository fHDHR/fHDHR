import sys
import time

# from fHDHR.exceptions import TunerError


class Direct_Stream():

    def __init__(self, fhdhr, stream_args, tuner):
        self.fhdhr = fhdhr
        self.stream_args = stream_args
        self.tuner = tuner

        self.bytes_per_read = int(self.fhdhr.config.dict["streaming"]["bytes_per_read"])

    def get(self):

        if not self.stream_args["duration"] == 0:
            self.stream_args["time_end"] = self.stream_args["duration"] + time.time()

        self.fhdhr.logger.info("Direct Stream of %s URL: %s" % (self.stream_args["true_content_type"], self.stream_args["stream_info"]["url"]))

        req = self.fhdhr.web.session.get(self.stream_args["stream_info"]["url"], stream=True)

        def generate():

            try:

                chunk_counter = 1

                while self.tuner.tuner_lock.locked():

                    for chunk in req.iter_content(chunk_size=self.bytes_per_read):

                        if (not self.stream_args["duration"] == 0 and
                           not time.time() < self.stream_args["time_end"]):
                            req.close()
                            self.fhdhr.logger.info("Requested Duration Expired.")
                            self.tuner.close()

                        if not chunk:
                            break
                            # raise TunerError("807 - No Video Data")

                        chunk_size = int(sys.getsizeof(chunk))
                        self.fhdhr.logger.info("Passing Through Chunk #%s with size %s" % (chunk_counter, chunk_size))
                        yield chunk
                        self.tuner.add_downloaded_size(chunk_size)

                        chunk_counter += 1

                self.fhdhr.logger.info("Connection Closed: Tuner Lock Removed")

            except GeneratorExit:
                self.fhdhr.logger.info("Connection Closed.")
            except Exception as e:
                self.fhdhr.logger.info("Connection Closed: %s" % e)
            finally:
                req.close()
                self.fhdhr.logger.info("Connection Closed: Tuner Lock Removed")
                self.tuner.close()
                # raise TunerError("806 - Tune Failed")

        return generate()
