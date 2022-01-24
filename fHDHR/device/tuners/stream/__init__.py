import sys
import datetime
from collections import OrderedDict


from .direct_http_stream import Direct_HTTP_Stream
from .direct_http_stream import Direct_FILE_Stream
from .direct_m3u8_stream import Direct_M3U8_Stream
from .direct_rtp_stream import Direct_RTP_Stream
from .direct_udp_stream import Direct_UDP_Stream
from .direct_hardware_stream import Direct_HardWare_Stream

from fHDHR.exceptions import TunerError


class Stream():
    """
    fHDHR Stream Management system.
    """

    def __init__(self, fhdhr, stream_args, tuner):
        self.fhdhr = fhdhr
        self.tuner = tuner
        self.stream_args = stream_args
        self.buffer_size = int(self.fhdhr.config.dict["streaming"]["buffer_size"])
        self.stream_restore_attempts = int(self.fhdhr.config.dict["streaming"]["stream_restore_attempts"])

        self.stream_setup()

    def stream_setup(self):

        if self.stream_args["method"] == "direct":

            # Select the HTTP stream method for HTTP/s addresses
            if (self.stream_args["stream_info"]["url"].startswith(tuple(["http://", "https://"]))
               and not self.stream_args["true_content_type"].startswith(tuple(["application/", "text/"]))):
                self.fhdhr.logger.info("Stream Method Detected as HTTP/s.")
                self.method = Direct_HTTP_Stream(self.fhdhr, self.stream_args, self.tuner)

            # Select the FILE method for file:// PATHS
            elif (self.stream_args["stream_info"]["url"].startswith(tuple(["file://"]))
                  and not self.stream_args["true_content_type"].startswith(tuple(["file://dev/"]))):
                self.fhdhr.logger.info("Stream Method Detected as file://.")
                self.method = Direct_FILE_Stream(self.fhdhr, self.stream_args, self.tuner)

            # Select the M3U8 stream method for hadnling M3U/8 streams
            elif self.stream_args["true_content_type"].startswith(tuple(["application/", "text/"])):
                self.fhdhr.logger.info("Stream Method Detected as M3U8.")
                self.method = Direct_M3U8_Stream(self.fhdhr, self.stream_args, self.tuner)

            # Select the RTP stream method for RTP/s addresses
            elif self.stream_args["stream_info"]["url"].startswith(tuple(["rtp://", "rtsp://"])):
                self.fhdhr.logger.info("Stream Method Detected as RTP/s.")
                self.method = Direct_RTP_Stream(self.fhdhr, self.stream_args, self.tuner)

            # Select the UDP stream method for UDP addresses
            elif self.stream_args["stream_info"]["url"].startswith(tuple(["udp://"])):
                self.fhdhr.logger.info("Stream Method Detected as UDP.")
                self.method = Direct_UDP_Stream(self.fhdhr, self.stream_args, self.tuner)

            # Select the HardWare stream method for /dev/ hardware devices
            elif self.stream_args["stream_info"]["url"].startswith(tuple(["/dev/", "file://dev/"])):
                self.fhdhr.logger.info("Stream Method Detected as a /dev/ hardware device.")
                self.method = Direct_HardWare_Stream(self.fhdhr, self.stream_args, self.tuner)

            # Select the Direct HTTP stream method as a fallback
            else:
                self.fhdhr.logger.warning("Stream Method couldn't be properly determined, defaulting to HTTP method.")
                self.method = Direct_HTTP_Stream(self.fhdhr, self.stream_args, self.tuner)

        else:

            plugin_name = self.get_alt_stream_plugin(self.stream_args["method"])
            if plugin_name:

                try:
                    self.method = self.fhdhr.plugins.plugins[plugin_name].Plugin_OBJ(self.fhdhr, self.fhdhr.plugins.plugins[plugin_name].plugin_utils, self.stream_args, self.tuner)

                except TunerError as e:
                    raise TunerError("Tuner Setup Failed: %s" % e)

                except Exception as e:
                    raise TunerError("Tuner Setup Failed: %s" % e)

            else:
                raise TunerError("806 - Tune Failed: Plugin Not Found")

    def stream_restore(self):

        self.stream_args = self.fhdhr.device.tuners.get_stream_info(self.stream_args)

        self.tuner.set_status(self.stream_args)

        self.tuner.setup_stream(self.stream_args, self.tuner)

        self.stream_setup()

    def get_alt_stream_plugin(self, method):
        """
        Import Stream Plugins.
        """

        for plugin_name in list(self.fhdhr.plugins.plugins.keys()):

            if self.fhdhr.plugins.plugins[plugin_name].type == "alt_stream":

                if self.fhdhr.plugins.plugins[plugin_name].name == method:
                    return plugin_name

        return None

    def get(self):
        """
        Handle a stream.
        """

        if self.stream_args["method"] == "direct":
            if self.stream_args["transcode_quality"]:
                self.fhdhr.logger.info("Client requested a %s transcode for stream. Direct Method cannot transcode." % self.stream_args["transcode_quality"])

        def buffer_generator():
            start_time = datetime.datetime.utcnow()
            segments_dict = OrderedDict()
            chunks_counter = 0

            try:
                while self.tuner.tuner_lock.locked():
                    chunks_failure = 0

                    for chunk in self.method.get():
                        chunks_counter += 1

                        if not chunk:
                            self.fhdhr.logger.warning("Chunk #%s Failed: No Chunk to add to stream. Possible Stream Source Failure." % chunks_counter)
                            chunks_failure += 1

                            if chunks_failure > self.stream_restore_attempts:
                                self.fhdhr.logger.warning("Attempts to restore stream exhausted: Limit %s." % self.stream_restore_attempts)
                                break

                            self.fhdhr.logger.warning("Attempting to restore stream: %s/%s." % (chunks_failure, self.stream_restore_attempts))

                            try:
                                self.stream_restore()
                            except TunerError as e:
                                self.fhdhr.logger.error("Unable to Restore Stream: %s" % e)
                                break

                        else:
                            chunks_failure = 0

                            segments_dict[chunks_counter] = chunk
                            self.fhdhr.logger.debug("Adding Chunk #%s to the buffer." % chunks_counter)
                            chunk_size = int(sys.getsizeof(chunk))
                            self.tuner.add_downloaded_size(chunk_size)

                            if len(list(segments_dict.items())) >= self.buffer_size:
                                chunk_number = list(segments_dict.keys())[0]
                                yield_chunk = segments_dict[chunk_number]

                                chunk_size = int(sys.getsizeof(yield_chunk))
                                self.fhdhr.logger.debug("Serving Chunk #%s: size %s" % (chunk_number, chunk_size))
                                yield yield_chunk

                                self.tuner.add_served_size(chunk_size)

                                self.fhdhr.logger.debug("Removing chunk #%s from the buffer." % chunk_number)
                                del segments_dict[chunk_number]

                            runtime = (datetime.datetime.utcnow() - start_time).total_seconds()
                            if self.stream_args["duration"]:
                                if runtime >= self.stream_args["duration"]:
                                    self.fhdhr.logger.info("Requested Duration Expired.")

            except GeneratorExit:
                self.fhdhr.logger.info("Stream Ended: Client has disconnected.")

            except Exception as e:
                self.fhdhr.logger.warning("Stream Ended: %s" % e)

            finally:

                self.fhdhr.logger.info("Removing Tuner Lock")
                self.tuner.close()

                if len(segments_dict.keys()):
                    self.fhdhr.logger.info("Removing %s chunks from the buffer." % len(segments_dict.keys()))
                    segments_dict = OrderedDict()

                if hasattr(self.fhdhr.origins.origins_dict[self.tuner.origin], "close_stream"):
                    self.fhdhr.logger.info("Running %s close_stream method." % self.tuner.origin)
                    self.fhdhr.origins.origins_dict[self.tuner.origin].close_stream(self.tuner.number, self.stream_args)

        return buffer_generator()
