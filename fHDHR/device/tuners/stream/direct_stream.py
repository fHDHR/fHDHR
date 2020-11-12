
import time
import re
import urllib.parse

# from fHDHR.exceptions import TunerError


class Direct_Stream():

    def __init__(self, fhdhr, stream_args, tuner):
        self.fhdhr = fhdhr
        self.stream_args = stream_args
        self.tuner = tuner

        self.chunksize = int(self.fhdhr.config.dict["direct_stream"]['chunksize'])

    def get(self):

        if not self.stream_args["duration"] == 0:
            self.stream_args["time_end"] = self.stream_args["duration"] + time.time()

        if not re.match('^(.*m3u8)[\n\r]*$', self.stream_args["channelUri"]):

            self.fhdhr.logger.info("Direct Stream of URL: %s" % self.stream_args["channelUri"])

            req = self.fhdhr.web.session.get(self.stream_args["channelUri"], stream=True)

            def generate():
                try:
                    while self.tuner.tuner_lock.locked():

                        for chunk in req.iter_content(chunk_size=self.chunksize):

                            if (not self.stream_args["duration"] == 0 and
                               not time.time() < self.stream_args["time_end"]):
                                req.close()
                                self.fhdhr.logger.info("Requested Duration Expired.")
                                self.tuner.close()

                            if not chunk:
                                break
                                # raise TunerError("807 - No Video Data")
                            yield chunk
                    self.fhdhr.logger.info("Connection Closed: Tuner Lock Removed")

                except GeneratorExit:
                    self.fhdhr.logger.info("Connection Closed.")
                except Exception as e:
                    self.fhdhr.logger.info("Connection Closed: " + str(e))
                finally:
                    req.close()
                    self.tuner.close()
                    # raise TunerError("806 - Tune Failed")

        else:

            self.fhdhr.logger.info("Detected stream URL is m3u8: %s" % self.stream_args["true_content_type"])

            # Determine if this m3u8 contains variants or chunks
            channelUri = self.stream_args["channelUri"]
            self.fhdhr.logger.info("Opening m3u8 URL: %s" % channelUri)
            m3u8_get = self.fhdhr.web.session.get(self.stream_args["channelUri"])
            m3u8_content = m3u8_get.text
            variants = [urllib.parse.urljoin(self.stream_args["channelUri"], line) for line in m3u8_content.split('\n') if re.match('^(.*m3u8)[\n\r]*$', line)]
            if len(variants):
                channelUri = variants[0]
                self.fhdhr.logger.info("m3u8 contained variants. Using URL: %s" % channelUri)

            def generate():

                try:

                    played_chunk_urls = []

                    while self.tuner.tuner_lock.locked():

                        m3u8_get = self.fhdhr.web.session.get(channelUri)
                        m3u8_content = m3u8_get.text
                        chunk_urls_detect = [urllib.parse.urljoin(channelUri, line) for line in m3u8_content.split('\n') if re.match('^(.*ts)[\n\r]*$', line)]

                        chunk_urls_play = []
                        for chunkurl in chunk_urls_detect:
                            if chunkurl not in played_chunk_urls:
                                chunk_urls_play.append(chunkurl)
                            played_chunk_urls.append(chunkurl)

                        for chunkurl in chunk_urls_play:

                            self.fhdhr.logger.info("Passing Through Chunk: %s" % chunkurl)

                            if (not self.stream_args["duration"] == 0 and
                               not time.time() < self.stream_args["time_end"]):
                                self.fhdhr.logger.info("Requested Duration Expired.")
                                self.tuner.close()

                            chunk = self.fhdhr.web.session.get(chunkurl).content
                            if not chunk:
                                break
                                # raise TunerError("807 - No Video Data")
                            yield chunk
                    self.fhdhr.logger.info("Connection Closed: Tuner Lock Removed")

                except GeneratorExit:
                    self.fhdhr.logger.info("Connection Closed.")
                except Exception as e:
                    self.fhdhr.logger.info("Connection Closed: " + str(e))
                finally:
                    self.tuner.close()
                    # raise TunerError("806 - Tune Failed")

        return generate()
