import sys
import datetime
from collections import OrderedDict


from .direct_stream import Direct_Stream
from .direct_m3u8_stream import Direct_M3U8_Stream
from fHDHR.exceptions import TunerError


class Stream():

    def __init__(self, fhdhr, stream_args, tuner):
        self.fhdhr = fhdhr
        self.tuner = tuner
        self.stream_args = stream_args
        self.buffer_size = int(self.fhdhr.config.dict["streaming"]["buffer_size"])

        if stream_args["method"] == "direct":
            if self.stream_args["true_content_type"].startswith(tuple(["application/", "text/"])):
                self.method = Direct_M3U8_Stream(fhdhr, stream_args, tuner)
            else:
                self.method = Direct_Stream(fhdhr, stream_args, tuner)
        else:
            plugin_name = self.get_alt_stream_plugin(stream_args["method"])
            if plugin_name:
                self.method = self.fhdhr.plugins.plugins[plugin_name].Plugin_OBJ(fhdhr, self.fhdhr.plugins.plugins[plugin_name].plugin_utils, stream_args, tuner)
            else:
                raise TunerError("806 - Tune Failed: Plugin Not Found")

    def get_alt_stream_plugin(self, method):
        for plugin_name in list(self.fhdhr.plugins.plugins.keys()):
            if self.fhdhr.plugins.plugins[plugin_name].type == "alt_stream":
                if self.fhdhr.plugins.plugins[plugin_name].name == method:
                    return plugin_name
        return None

    def get(self):
        def buffer_generator():
            start_time = datetime.datetime.utcnow()
            segments_dict = OrderedDict()
            chunks_counter = 0

            try:
                while self.tuner.tuner_lock.locked():
                    for chunk in self.method.get():
                        chunks_counter += 1

                        if not chunk:
                            break

                        segments_dict[chunks_counter] = chunk
                        self.fhdhr.logger.debug("Adding Chunk #%s to the buffer." % chunks_counter)
                        chunk_size = int(sys.getsizeof(chunk))
                        self.tuner.add_downloaded_size(chunk_size)

                        if len(list(segments_dict.items())) >= self.buffer_size:
                            chunk_number = list(segments_dict.keys())[0]
                            yield_chunk = segments_dict[chunk_number]

                            chunk_size = int(sys.getsizeof(yield_chunk))
                            self.fhdhr.logger.info("Serving Chunk #%s: size %s" % (chunk_number, chunk_size))
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
                self.fhdhr.logger.info("Stream Ended: %s" % e)

            finally:

                self.fhdhr.logger.info("Removing Tuner Lock")
                self.tuner.close()

                if hasattr(self.fhdhr.origins.origins_dict[self.tuner.origin], "close_stream"):
                    self.fhdhr.logger.info("Running %s close_stream method." % self.tuner.origin)
                    self.fhdhr.origins.origins_dict[self.tuner.origin].close_stream(self.tuner.number, self.stream_args)

        return buffer_generator()
