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

        self.bytes_per_read = int(self.fhdhr.config.dict["streaming"]["bytes_per_read"])

        try:

            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_socket.bind((self.address, 0))
            self.udp_socket_address = self.udp_socket.getsockname()[0]
            self.udp_socket_port = self.udp_socket.getsockname()[1]
            self.udp_socket.settimeout(5)
            self.fhdhr.logger.info("Created UDP socket at %s:%s." % (self.udp_socket_address, self.udp_socket_port))

        except Exception as err:
            raise TunerError("806 - Tune Failed: %s" % err)

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

                    chunk, addr = self.udp_socket.recvfrom(self.bytes_per_read)

                    if not chunk:
                        break

                    yield chunk

            except Exception as err:
                self.fhdhr.logger.error("Chunk #%s unable to process: %s" % (chunk_counter, err))

            finally:
                self.fhdhr.logger.info("Closing UDP socket at %s:%s." % (self.udp_socket_address, self.udp_socket_port))
                self.udp_socket.close()

        return generate()
