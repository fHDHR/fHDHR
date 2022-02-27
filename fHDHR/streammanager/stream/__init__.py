import sys
import datetime
from collections import OrderedDict


from .direct_http_stream import Direct_HTTP_Stream
from .direct_file_stream import Direct_FILE_Stream
from .direct_m3u8_stream import Direct_M3U8_Stream
from .direct_rtp_stream import Direct_RTP_Stream
from .direct_udp_stream import Direct_UDP_Stream
from .direct_hardware_stream import Direct_HardWare_Stream

from fHDHR.exceptions import TunerError
from fHDHR.tools import checkattr


class Stream():
    """
    fHDHR Stream Management system.
    """

    def __init__(self, fhdhr, tuner, stream_obj):
        self.fhdhr = fhdhr
        self.tuner = tuner
        self.stream_obj = stream_obj

        self.stream_setup()

    def stream_setup(self):

        if self.stream_obj.stream_args["method"] == "direct":

            # Select the HTTP stream method for HTTP/s addresses
            if (self.stream_obj.stream_args["stream_info"]["url"].startswith(tuple(["http://", "https://"]))
               and not self.stream_obj.stream_args["true_content_type"].startswith(tuple(["application/", "text/"]))):
                self.fhdhr.logger.info("Stream Method Detected as HTTP/s.")
                self.method = Direct_HTTP_Stream(self.fhdhr, self.stream_obj.stream_args, self.tuner)

            # Select the FILE method for file:// PATHS
            elif (self.stream_obj.stream_args["stream_info"]["url"].startswith(tuple(["file://"]))
                  and not self.stream_obj.stream_args["true_content_type"].startswith(tuple(["file://dev/"]))):
                self.fhdhr.logger.info("Stream Method Detected as file://.")
                self.method = Direct_FILE_Stream(self.fhdhr, self.stream_obj.stream_args, self.tuner)

            # Select the M3U8 stream method for hadnling M3U/8 streams
            elif self.stream_obj.stream_args["true_content_type"].startswith(tuple(["application/", "text/"])):
                self.fhdhr.logger.info("Stream Method Detected as M3U8.")
                self.method = Direct_M3U8_Stream(self.fhdhr, self.stream_obj.stream_args, self.tuner)

            # Select the RTP stream method for RTP/s addresses
            elif self.stream_obj.stream_args["stream_info"]["url"].startswith(tuple(["rtp://", "rtsp://"])):
                self.fhdhr.logger.info("Stream Method Detected as RTP/s.")
                self.method = Direct_RTP_Stream(self.fhdhr, self.stream_obj.stream_args, self.tuner)

            # Select the UDP stream method for UDP addresses
            elif self.stream_obj.stream_args["stream_info"]["url"].startswith(tuple(["udp://"])):
                self.fhdhr.logger.info("Stream Method Detected as UDP.")
                self.method = Direct_UDP_Stream(self.fhdhr, self.stream_obj.stream_args, self.tuner)

            # Select the HardWare stream method for /dev/ hardware devices
            elif self.stream_obj.stream_args["stream_info"]["url"].startswith(tuple(["/dev/", "file://dev/"])):
                self.fhdhr.logger.info("Stream Method Detected as a /dev/ hardware device.")
                self.method = Direct_HardWare_Stream(self.fhdhr, self.stream_obj.stream_args, self.tuner)

            # Select the Direct HTTP stream method as a fallback
            else:
                self.fhdhr.logger.warning("Stream Method couldn't be properly determined, defaulting to HTTP method.")
                self.method = Direct_HTTP_Stream(self.fhdhr, self.stream_obj.stream_args, self.tuner)

        else:

            plugin_name = self.get_alt_stream_plugin(self.stream_obj.stream_args["method"])
            if plugin_name:

                try:
                    self.method = self.fhdhr.plugins.plugins[plugin_name].Plugin_OBJ(self.fhdhr, self.fhdhr.plugins.plugins[plugin_name].plugin_utils, self.stream_obj.stream_args, self.tuner)

                except TunerError as exerror:
                    raise TunerError("Tuner Setup Failed: %s" % exerror)

                except Exception as exerror:
                    error_out = self.fhdhr.logger.lazy_exception("Tuner Setup Failed (lazily handled)", exerror)
                    raise TunerError(error_out)

            else:
                raise TunerError("806 - Tune Failed: %s Plugin Not Found." % self.stream_obj.stream_args["method"])

    def stream_restore(self):

        self.stream_obj.stream_restore()

        self.tuner.set_status(self.stream_obj.stream_args)

        self.stream_setup()

    def get_alt_stream_plugin(self, method):
        """
        Import Stream Plugins.
        """

        for plugin_name in self.fhdhr.plugins.search_by_type("alt_stream"):

            if self.fhdhr.plugins.plugins[plugin_name].name == method:
                return plugin_name

        return None

    def get(self):
        """
        Handle a stream.
        """

        self.fhdhr.logger.info("Tuning Stream...")

        if self.stream_obj.stream_args["method"] == "direct":

            if self.stream_obj.stream_args["transcode_quality"]:
                self.fhdhr.logger.info("Client requested a %s transcode for stream. Direct Method cannot transcode." % self.stream_obj.stream_args["transcode_quality"])

            if self.stream_obj.stream_args["stream_info"]["url"].endswith(".m3u8"):
                self.fhdhr.logger.info("Client requested a %s bytes_per_read for stream. Direct M3U8 Method reads the chunks as provided." % self.stream_obj.stream_args["bytes_per_read"])

        def buffer_generator():
            start_time = datetime.datetime.utcnow()
            segments_dict = OrderedDict()
            chunks_counter = 0

            try:
                while self.tuner.tuner_lock.locked():
                    chunks_failure = 0
                    stream_failure = False

                    for chunk in self.method.get():

                        chunks_counter += 1

                        if not chunk:
                            self.fhdhr.logger.warning("Chunk #%s Failed: No Chunk to add to stream. Possible Stream Source Failure." % chunks_counter)
                            chunks_failure += 1

                            if chunks_failure > self.stream_obj.stream_args["stream_restore_attempts"]:
                                self.fhdhr.logger.warning("Attempts to restore stream exhausted: Limit %s." % self.stream_obj.stream_args["stream_restore_attempts"])
                                stream_failure = True

                            else:
                                self.fhdhr.logger.warning("Attempting to restore stream: %s/%s." % (chunks_failure, self.stream_obj.stream_args["stream_restore_attempts"]))
                                try:
                                    self.stream_restore()
                                except TunerError as exerror:
                                    self.fhdhr.logger.error("Unable to Restore Stream: %s" % exerror)
                                    stream_failure = True

                        else:
                            chunks_failure = 0

                            segments_dict[chunks_counter] = chunk
                            self.fhdhr.logger.debug("Adding Chunk #%s to the buffer." % chunks_counter)
                            chunk_size = int(sys.getsizeof(chunk))
                            self.stream_obj.add_downloaded_size(chunk_size, chunks_counter)

                        buffer_chunk_script = "Buffer has %s/%s chunks. " % (len(list(segments_dict.items())), self.stream_obj.stream_args["buffer_size"])

                        # If Buffer is up to buffer_size, serve chunk
                        if len(list(segments_dict.items())) >= self.stream_obj.stream_args["buffer_size"]:
                            buffer_chunk_script += "Allowing buffer reduction due to buffer at capacity. "
                            yield_chunks = 1

                        # Allow serving first chunk right away for client speed
                        # we'll hope the buffer can fill up before needing a second one
                        # elif list(segments_dict.keys())[0] == 1:
                        #    buffer_chunk_script += "Allowing buffer bypass to serve first chunk to client. "
                        #    yield_chunks = 1

                        # OR the stream has been marked as failed, we might as well serve remaining chunks
                        elif stream_failure and len(list(segments_dict.items())):
                            buffer_chunk_script += "Allowing buffer depletion due to failed stream. "
                            yield_chunks = len(list(segments_dict.items()))

                        # yield a chunk after a chunk failure even if the buffer isn't to the maximum
                        elif chunks_failure and len(list(segments_dict.items())):
                            buffer_chunk_script += "Allowing buffer reduction due to dropped stream. "
                            yield_chunks = 1

                        elif len(list(segments_dict.items())) < self.stream_obj.stream_args["buffer_size"]:
                            buffer_chunk_script += "Continuing to build buffer. "
                            yield_chunks = 0

                        # if not above condition, allow the buffer to build before serving
                        else:
                            yield_chunks = 0
                            # TODO maybe a fHDHR splash screen to show it is working

                        if yield_chunks:

                            buffer_chunk_script += "Serving %s chunk(s)." % yield_chunks
                            self.fhdhr.logger.debug(buffer_chunk_script)

                            for chunk_yield in range(yield_chunks):

                                chunk_number = list(segments_dict.keys())[chunk_yield]
                                yield_chunk = segments_dict[chunk_number]

                                chunk_size = int(sys.getsizeof(yield_chunk))
                                self.fhdhr.logger.debug("Serving Chunk #%s: size %s" % (chunk_number, chunk_size))
                                yield yield_chunk

                                self.stream_obj.add_served_size(chunk_size, chunk_number)

                                self.fhdhr.logger.debug("Removing chunk #%s from the buffer." % chunk_number)
                                del segments_dict[chunk_number]

                        else:
                            buffer_chunk_script += "Not Serving chunk(s)."
                            self.fhdhr.logger.debug(buffer_chunk_script)

                        # If the stream has failed
                        if stream_failure:
                            break

                        # Kill stream if duration has been passed
                        elif self.stream_obj.stream_args["duration"]:
                            runtime = (datetime.datetime.utcnow() - start_time).total_seconds()
                            if runtime >= self.stream_obj.stream_args["duration"]:
                                self.fhdhr.logger.info("Requested Duration Expired.")
                                break

            except GeneratorExit:
                self.fhdhr.logger.info("Stream Ended: Client has disconnected.")

            except Exception as exerror:
                self.fhdhr.logger.warning("Stream Ended: %s" % exerror)

            finally:

                self.fhdhr.logger.info("Removing Tuner Lock")
                self.tuner.close()

                if len(segments_dict.keys()):
                    self.fhdhr.logger.info("Removing %s chunks from the buffer." % len(segments_dict.keys()))
                    segments_dict = OrderedDict()

                if checkattr(self.stream_obj.origin_plugin, "close_stream"):
                    self.fhdhr.logger.info("Running %s close_stream method." % self.stream_obj.origin)
                    self.stream_obj.origin_plugin.close_stream(self.tuner.number, self.stream_obj.stream_args)

        def unbuffered_generator():
            start_time = datetime.datetime.utcnow()
            chunks_counter = 0

            try:
                while self.tuner.tuner_lock.locked():
                    chunks_failure = 0
                    stream_failure = False

                    for chunk in self.method.get():

                        chunks_counter += 1

                        if not chunk:
                            self.fhdhr.logger.warning("Chunk #%s Failed: No Chunk to add to stream. Possible Stream Source Failure." % chunks_counter)
                            chunks_failure += 1

                            if chunks_failure > self.stream_obj.stream_args["stream_restore_attempts"]:
                                self.fhdhr.logger.warning("Attempts to restore stream exhausted: Limit %s." % self.stream_obj.stream_args["stream_restore_attempts"])
                                stream_failure = True

                            else:
                                self.fhdhr.logger.warning("Attempting to restore stream: %s/%s." % (chunks_failure, self.stream_obj.stream_args["stream_restore_attempts"]))
                                try:
                                    self.stream_restore()
                                except TunerError as exerror:
                                    self.fhdhr.logger.error("Unable to Restore Stream: %s" % exerror)
                                    stream_failure = True

                        else:
                            chunks_failure = 0

                            chunk_size = int(sys.getsizeof(chunk))
                            self.stream_obj.add_downloaded_size(chunk_size, chunks_counter)

                            self.fhdhr.logger.debug("Serving Chunk #%s: size %s" % (chunks_counter, chunk_size))

                            yield chunk
                            self.stream_obj.add_served_size(chunk_size, chunks_counter)

                        # If the stream has failed
                        if stream_failure:
                            break

                        # Kill stream if duration has been passed
                        elif self.stream_obj.stream_args["duration"]:
                            runtime = (datetime.datetime.utcnow() - start_time).total_seconds()
                            if runtime >= self.stream_obj.stream_args["duration"]:
                                self.fhdhr.logger.info("Requested Duration Expired.")
                                break

            except GeneratorExit:
                self.fhdhr.logger.info("Stream Ended: Client has disconnected.")

            except Exception as exerror:
                self.fhdhr.logger.warning("Stream Ended: %s" % exerror)

            finally:

                self.fhdhr.logger.info("Removing Tuner Lock")
                self.tuner.close()

                if checkattr(self.stream_obj.origin_plugin, "close_stream"):
                    self.fhdhr.logger.info("Running %s close_stream method." % self.stream_obj.origin)
                    self.stream_obj.origin_plugin.close_stream(self.tuner.number, self.stream_obj.stream_args)

        if self.stream_obj.stream_args["buffer_size"] in [0, None, "0"]:
            self.fhdhr.logger.info("Stream will not use Any Buffering.")
            return unbuffered_generator()
        else:
            return buffer_generator()
