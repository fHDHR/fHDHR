import sys
import time
import datetime
import m3u8
from collections import OrderedDict
from Crypto.Cipher import AES

# from fHDHR.exceptions import TunerError


class Direct_M3U8_Stream():

    def __init__(self, fhdhr, stream_args, tuner):
        self.fhdhr = fhdhr
        self.stream_args = stream_args
        self.tuner = tuner

        self.bytes_per_read = int(self.fhdhr.config.dict["streaming"]["bytes_per_read"])

    def get(self):

        self.fhdhr.logger.info("Detected stream of m3u8 URL: %s" % self.stream_args["stream_info"]["url"])

        if self.stream_args["transcode_quality"]:
            self.fhdhr.logger.info("Client requested a %s transcode for stream. Direct Method cannot transcode." % self.stream_args["transcode_quality"])

        def generate():

            try:
                segments_dict = OrderedDict()
                start_time = datetime.datetime.utcnow()
                total_secs_served = 0
                chunks_counter = 0

                while self.tuner.tuner_lock.locked():

                    added, removed = 0, 0

                    # (re)Load the m3u8 playlist, apply headers if needbe
                    try:
                        if self.stream_args["stream_info"]["headers"]:
                            playlist = m3u8.load(self.stream_args["stream_info"]["url"], headers=self.stream_args["stream_info"]["headers"])
                        else:
                            playlist = m3u8.load(self.stream_args["stream_info"]["url"])
                    except Exception as e:
                        self.fhdhr.logger.info("Connection Closed: %s" % e)
                        self.tuner.close()
                        return None

                    m3u8_segments = playlist.segments

                    if playlist.keys != [None]:
                        keys = [{"uri": key.absolute_uri, "method": key.method, "iv": key.iv} for key in playlist.keys if key]
                    else:
                        keys = [None for i in range(0, len(m3u8_segments))]

                    # Only add new m3u8_segments to our segments_dict
                    for segment, key in zip(m3u8_segments, keys):
                        uri = segment.absolute_uri
                        if uri not in list(segments_dict.keys()):
                            chunks_counter += 1
                            segments_dict[uri] = {
                                                  "played": False,
                                                  "duration": segment.duration,
                                                  "chunk_number": chunks_counter,
                                                  "key": key
                                                  }
                            added += 1
                            self.fhdhr.logger.debug("Adding %s to play queue." % uri)

                        segments_dict[uri]["last_seen"] = datetime.datetime.utcnow()

                    # Cleanup Play Queue
                    for uri, data in list(segments_dict.items()):
                        if data["played"] and (datetime.datetime.utcnow() - data["last_seen"]).total_seconds() > 10:
                            self.fhdhr.logger.debug("Removed %s from play queue." % uri)
                            del segments_dict[uri]
                            removed += 1

                    self.fhdhr.logger.info("Refreshing m3u8, Loaded %s new segments, removed %s" % (added, removed))

                    for uri, data in list(segments_dict.items()):

                        if not data["played"]:

                            self.fhdhr.logger.debug("Downloading Chunk #%s: %s" % (data["chunk_number"], uri))
                            if self.stream_args["stream_info"]["headers"]:
                                chunk = self.fhdhr.web.session.get(uri, headers=self.stream_args["stream_info"]["headers"]).content
                            else:
                                chunk = self.fhdhr.web.session.get(uri).content

                            if data["key"]:
                                if data["key"]["uri"]:
                                    if self.stream_args["stream_info"]["headers"]:
                                        keyfile = self.fhdhr.web.session.get(data["key"]["uri"], headers=self.stream_args["stream_info"]["headers"]).content
                                    else:
                                        keyfile = self.fhdhr.web.session.get(data["key"]["uri"]).content
                                    cryptor = AES.new(keyfile, AES.MODE_CBC, keyfile)
                                    self.fhdhr.logger.debug("Decrypting Chunk #%s with key: %s" % (data["chunk_number"], data["key"]["uri"]))
                                    chunk = cryptor.decrypt(chunk)

                            segments_dict[uri]["played"] = True

                            if not chunk:
                                break
                                # raise TunerError("807 - No Video Data")

                            duration = data['duration']
                            runtime = (datetime.datetime.utcnow() - start_time).total_seconds()
                            target_diff = 0.5 * duration

                            if total_secs_served > 0:
                                wait = total_secs_served - target_diff - runtime
                            else:
                                wait = 0

                            total_secs_served += duration

                            chunk_size = int(sys.getsizeof(chunk))
                            self.fhdhr.logger.info("Passing Through Chunk #%s: size %s, duration %s" % (data["chunk_number"], chunk_size, duration))
                            yield chunk
                            self.tuner.add_downloaded_size(chunk_size)

                            # We can't wait negative time..
                            if wait > 0:
                                time.sleep(wait)

                            if self.stream_args["duration"]:
                                if (total_secs_served >= int(self.stream_args["duration"])) or (runtime >= self.stream_args["duration"]):
                                    self.fhdhr.logger.info("Requested Duration Expired.")
                                    self.tuner.close()

                self.fhdhr.logger.info("Connection Closed: Tuner Lock Removed")

            except GeneratorExit:
                self.fhdhr.logger.info("Connection Closed.")
            except Exception as e:
                self.fhdhr.logger.info("Connection Closed: %s" % e)
            finally:
                self.fhdhr.logger.info("Connection Closed: Tuner Lock Removed")
                if hasattr(self.fhdhr.origins.origins_dict[self.tuner.origin], "close_stream"):
                    self.fhdhr.origins.origins_dict[self.tuner.origin].close_stream(self.tuner.number, self.stream_args)
                self.tuner.close()
                # raise TunerError("806 - Tune Failed")

        return generate()
