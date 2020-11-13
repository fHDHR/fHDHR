import time
import m3u8

from Crypto.Cipher import AES

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

        if not self.stream_args["true_content_type"].startswith(tuple(["application/", "text/"])):

            self.fhdhr.logger.info("Direct Stream of %s URL: %s" % (self.stream_args["true_content_type"], self.stream_args["channelUri"]))

            req = self.fhdhr.web.session.get(self.stream_args["channelUri"], stream=True)

            def generate():

                try:

                    chunk_counter = 1

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

                            self.fhdhr.logger.info("Passing Through Chunk #%s with size %s" % (chunk_counter, self.chunksize))
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

            channelUri = self.stream_args["channelUri"]
            while True:

                videoUrlM3u = m3u8.load(channelUri)
                if len(videoUrlM3u.playlists):
                    channelUri = videoUrlM3u.playlists[0].absolute_uri
                else:
                    break

            def generate():

                try:

                    played_chunk_urls = []

                    while self.tuner.tuner_lock.locked():

                        playlist = m3u8.load(channelUri)
                        segments = playlist.segments

                        if len(played_chunk_urls):
                            newsegments = 0
                            for segment in segments:
                                if segment.absolute_uri not in played_chunk_urls:
                                    newsegments += 1
                            self.fhdhr.logger.info("Refreshing m3u8, Loaded %s new segments." % str(newsegments))
                        else:
                            self.fhdhr.logger.info("Loaded %s segments." % str(len(segments)))

                        if playlist.keys != [None]:
                            keys = [{"url": key.uri, "method": key.method, "iv": key.iv} for key in playlist.keys if key]
                        else:
                            keys = [None for i in range(0, len(segments))]

                        for segment, key in zip(segments, keys):
                            chunkurl = segment.absolute_uri

                            if chunkurl not in played_chunk_urls:
                                played_chunk_urls.append(chunkurl)

                                if (not self.stream_args["duration"] == 0 and
                                   not time.time() < self.stream_args["time_end"]):
                                    self.fhdhr.logger.info("Requested Duration Expired.")
                                    self.tuner.close()

                                chunk = self.fhdhr.web.session.get(chunkurl).content
                                if not chunk:
                                    break
                                    # raise TunerError("807 - No Video Data")
                                if key:
                                    keyfile = self.fhdhr.web.session.get(key["url"]).content
                                    cryptor = AES.new(keyfile, AES.MODE_CBC, keyfile)
                                    chunk = cryptor.decrypt(chunk)

                                self.fhdhr.logger.info("Passing Through Chunk: %s" % chunkurl)
                                yield chunk

                        if playlist.target_duration:
                            time.sleep(int(playlist.target_duration))

                    self.fhdhr.logger.info("Connection Closed: Tuner Lock Removed")

                except GeneratorExit:
                    self.fhdhr.logger.info("Connection Closed.")
                except Exception as e:
                    self.fhdhr.logger.info("Connection Closed: " + str(e))
                finally:
                    self.tuner.close()
                    # raise TunerError("806 - Tune Failed")

        return generate()
