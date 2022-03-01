import socket

from fHDHR.exceptions import TunerError

# TODO Needs more work, testing


class Direct_UDP_Stream():
    """
    A method to stream from /dev/ hardware devices directly.
    """

    def __init__(self, fhdhr, stream_args, tuner):
        self.fhdhr = fhdhr
        self.stream_args = stream_args
        self.tuner = tuner

        try:

            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_socket.bind((self.address, 0))
            self.udp_socket_address = self.udp_socket.getsockname()[0]
            self.udp_socket_port = self.udp_socket.getsockname()[1]
            self.udp_socket.settimeout(5)
            self.fhdhr.logger.info("Created UDP socket at %s:%s." % (self.udp_socket_address, self.udp_socket_port))

        except Exception as exerror:
            error_out = self.fhdhr.logger.lazy_exception(exerror, "806 - Tune Failed")
            raise TunerError(error_out)

        finally:
            self.fhdhr.logger.info("Closing UDP socket at %s:%s." % (self.udp_socket_address, self.udp_socket_port))
            self.udp_socket.close()

    def get(self):
        """
        Produce chunks of video data.
        """

        self.fhdhr.logger.info("Direct UDP Stream from device: %s" % (self.stream_args["stream_info"]["url"]))

        def generate():

            chunk_counter = 0

            try:
                while self.tuner.tuner_lock.locked():

                    chunk_counter += 1
                    self.fhdhr.logger.debug("Downloading Chunk #%s" % chunk_counter)

                    chunk, addr = self.udp_socket.recvfrom(self.stream_args["bytes_per_read"])

                    if not chunk:
                        break

                    yield chunk

            except Exception as exerror:
                error_out = self.fhdhr.logger.lazy_exception(exerror, "Chunk #%s unable to process" % chunk_counter)
                self.fhdhr.logger.error(error_out)

            finally:
                self.fhdhr.logger.info("Closing UDP socket at %s:%s." % (self.udp_socket_address, self.udp_socket_port))
                self.udp_socket.close()

        return generate()
