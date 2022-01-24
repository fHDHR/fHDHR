import socket
import re
import bitstring
import base64

from fHDHR.exceptions import TunerError

# TODO Needs more work, testing, and cleanup


class Direct_RTP_Stream():
    """
    A method to stream rtp/s.
    """

    def __init__(self, fhdhr, stream_args, tuner):
        self.fhdhr = fhdhr
        self.stream_args = stream_args
        self.tuner = tuner

        self.bytes_per_read = int(self.fhdhr.config.dict["streaming"]["bytes_per_read"])

        self.fhdhr.logger.info("Attempting to create socket to listen on.")
        self.address = self.get_sock_address()
        if not self.address:
            raise TunerError("806 - Tune Failed: Could Not Create Socket")

        try:
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.bind((self.address, 0))
            self.tcp_socket_address = self.tcp_socket.getsockname()[0]
            self.tcp_socket_port = self.tcp_socket.getsockname()[1]
            self.fhdhr.logger.info("Created TCP socket at %s:%s." % (self.tcp_socket_address, self.tcp_socket_port))

            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_socket.bind((self.address, 0))
            self.udp_socket_address = self.udp_socket.getsockname()[0]
            self.udp_socket_port = self.udp_socket.getsockname()[1]
            self.udp_socket.settimeout(5)
            self.fhdhr.logger.info("Created UDP socket at %s:%s." % (self.udp_socket_address, self.udp_socket_port))

            credentials = "%s:%s" % (self.stream_args["stream_info"]["username"], self.stream_args["stream_info"]["password"])
            credentials_bytes = credentials.encode("ascii")
            credentials_base64_bytes = base64.b64encode(credentials_bytes)
            credentials_base64_string = credentials_base64_bytes.decode("ascii")

            self.describe = "DESCRIBE %s RTSP/1.0\r\nCSeq: 2\r\nUser-Agent: python\r\nAccept: application/sdp\r\nAuthorization: Basic %s\r\n\r\n" % (self.stream_args["stream_info"]["url"], credentials_base64_string)
            self.setup = "SETUP %s/trackID=1 RTSP/1.0\r\nCSeq: 3\r\nUser-Agent: python\r\nTransport: RTP/AVP;unicast;client_port=%s\r\nAuthorization: Basic %s\r\n\r\n" % (self.stream_args["stream_info"]["url"], self.udp_socket_port, credentials_base64_string)

            self.fhdhr.logger.info("Connecting to Socket")
            self.tcp_socket.connect((self.stream_args["stream_info"]["address"], self.stream_args["stream_info"]["port"]))

            self.fhdhr.logger.info("Sending DESCRIBE")
            self.tcp_socket.send(self.describe.encode("utf-8"))
            recst = self.tcp_socket.recv(4096).decode()
            self.fhdhr.logger.info("Got response: %s" % recst)

            self.fhdhr.logger.info("Sending SETUP")
            self.tcp_socket.send(self.setup.encode("utf-8"))
            recst = self.tcp_socket.recv(4096).decode()
            self.fhdhr.logger.info("Got response: %s" % recst)

            self.sessionid = self.sessionid(recst)
            self.fhdhr.logger.info("SessionID=%s" % self.sessionid)
            self.play = "PLAY %s RTSP/1.0\r\nCSeq: 5\r\nUser-Agent: python\r\nSession: %s\r\nRange: npt=0.000-\r\nAuthorization: Basic %s\r\n\r\n" % (self.stream_args["stream_info"]["url"], self.sessionid, credentials_base64_string)

        except Exception as e:
            self.fhdhr.logger.info("Closing UDP socket at %s:%s." % (self.udp_socket_address, self.udp_socket_port))
            self.udp_socket.close()
            self.fhdhr.logger.info("Closing TCP socket at %s:%s." % (self.tcp_socket_address, self.tcp_socket_port))
            self.tcp_socket.close()
            raise TunerError("806 - Tune Failed: Could Not Create Socket: %s" % e)

    def get(self):
        """
        Produce chunks of video data.
        """

        self.fhdhr.logger.info("Direct Stream of %s URL: %s" % (self.stream_args["true_content_type"], self.stream_args["stream_info"]["url"]))

        self.fhdhr.logger.info("Sending PLAY")
        self.tcp_socket.send(self.play.encode("utf-8"))

        def generate():

            chunk_counter = 0

            try:

                while self.tuner.tuner_lock.locked():

                    chunk = self.udp_socket.recv(self.bytes_per_read)
                    chunk_counter += 1
                    self.fhdhr.logger.debug("Downloading Chunk #%s" % chunk_counter)

                    self.fhdhr.logger.debug("Stripping Chunk #%s RTP headers " % chunk_counter)
                    chunk = self.digestpacket(chunk)

                    if not chunk:
                        break

                    yield chunk

            finally:
                self.fhdhr.logger.info("Closing UDP socket at %s:%s." % (self.udp_socket_address, self.udp_socket_port))
                self.udp_socket.close()
                self.fhdhr.logger.info("Closing TCP socket at %s:%s." % (self.tcp_socket_address, self.tcp_socket_port))
                self.tcp_socket.close()

        return generate()

    def get_sock_address(self):
        if self.fhdhr.config.dict["fhdhr"]["discovery_address"]:
            return self.fhdhr.config.dict["fhdhr"]["discovery_address"]
        else:
            try:
                base_url = self.stream_args["base_url"].split("://")[1].split(":")[0]
            except IndexError:
                return None
            ip_match = re.match('^' + '[\.]'.join(['(\d{1,3})']*4) + '$', base_url)
            ip_validate = bool(ip_match)
            if ip_validate:
                return base_url
        return None

    def sessionid(self, recst):
        """ Search session id from rtsp strings
        """
        recs = recst.split('\r\n')
        for rec in recs:
            ss = rec.split()
            if (ss[0].strip() == "Session:"):
                return int(ss[1].split(";")[0].strip())

    def digestpacket(self, st):
        """ This routine takes a UDP packet, i.e. a string of bytes and ..
        (a) strips off the RTP header
        (b) adds NAL "stamps" to the packets, so that they are recognized as NAL's
        (c) Concantenates frames
        (d) Returns a packet that can be written to disk as such and that is recognized by stock media players as h264 stream
        """
        startbytes = "\x00\x00\x00\x01"  # this is the sequence of four bytes that identifies a NAL packet.. must be in front of every NAL packet.

        bt = bitstring.BitArray(bytes=st)  # turn the whole string-of-bytes packet into a string of bits.  Very unefficient, but hey, this is only for demoing.
        lc = 12  # bytecounter
        bc = 12 * 8  # bitcounter

        version = bt[0:2].uint  # version
        p = bt[3]  # P
        x = bt[4]  # X
        cc = bt[4:8].uint  # CC
        m = bt[9]  # M
        pt = bt[9:16].uint  # PT
        sn = bt[16:32].uint  # sequence number
        timestamp = bt[32:64].uint  # timestamp
        ssrc = bt[64:96].uint  # ssrc identifier
        # The header format can be found from:
        # https://en.wikipedia.org/wiki/Real-time_Transport_Protocol

        lc = 12  # so, we have red twelve bytes
        bc = 12 * 8  # .. and that many bits

        self.fhdhr.logger.debug("version:%s, p:%s, x:%s, cc:%s, m:%s, pt:%s" % (version, p, x, cc, m, pt))
        self.fhdhr.logger.debug("sequence number:%s, timestamp:%s" % (sn, timestamp))
        self.fhdhr.logger.debug("sync. source identifier:%s" % ssrc)

        # st=f.read(4*cc) # csrc identifiers, 32 bits (4 bytes) each
        cids = []
        for i in range(cc):
            cids.append(bt[bc:bc+32].uint)
            bc += 32
            lc += 4
            self.fhdhr.logger.debug("csrc identifiers:", cids)

        if (x):
            # this section haven't been tested.. might fail
            hid = bt[bc:bc+16].uint
            bc += 16
            lc += 2

            hlen = bt[bc:bc+16].uint
            bc += 16
            lc += 2

            self.fhdhr.logger.debug("ext. header id:%s, header len:%s" % (hid, hlen))

            # hst = bt[bc:bc+32*hlen]
            bc += 32 * hlen
            lc += 4 * hlen

        # OK, now we enter the NAL packet, as described here:
        #
        # https://tools.ietf.org/html/rfc6184#section-1.3
        #
        # Some quotes from that document:
        #
        """
        5.3. NAL Unit Header Usage
        The structure and semantics of the NAL unit header were introduced in
        Section 1.3.  For convenience, the format of the NAL unit header is
        reprinted below:
          +---------------+
          |0|1|2|3|4|5|6|7|
          +-+-+-+-+-+-+-+-+
          |F|NRI|  Type   |
          +---------------+
        This section specifies the semantics of F and NRI according to this
        specification.
        """
        """
        Table 3.  Summary of allowed NAL unit types for each packetization
                    mode (yes = allowed, no = disallowed, ig = ignore)
          Payload Packet    Single NAL    Non-Interleaved    Interleaved
          Type    Type      Unit Mode           Mode             Mode
          -------------------------------------------------------------
          0      reserved      ig               ig               ig
          1-23   NAL unit     yes              yes               no
          24     STAP-A        no              yes               no
          25     STAP-B        no               no              yes
          26     MTAP16        no               no              yes
          27     MTAP24        no               no              yes
          28     FU-A          no              yes              yes
          29     FU-B          no               no              yes
          30-31  reserved      ig               ig               ig
        """
        # This was also very usefull:
        # http://stackoverflow.com/questions/7665217/how-to-process-raw-udp-packets-so-that-they-can-be-decoded-by-a-decoder-filter-i
        # A quote from that:
        """
        First byte:  [ 3 NAL UNIT BITS | 5 FRAGMENT TYPE BITS]
        Second byte: [ START BIT | RESERVED BIT | END BIT | 5 NAL UNIT BITS]
        Other bytes: [... VIDEO FRAGMENT DATA...]
        """

        fb = bt[bc]  # i.e. "F"
        nri = bt[bc+1:bc+3].uint  # "NRI"
        nlu0 = bt[bc:bc+3]  # "3 NAL UNIT BITS" (i.e. [F | NRI])
        typ = bt[bc+3:bc+8].uint  # "Type"
        self.fhdhr.logger.debug("F:%s, NRI:%s, Type:%s" % (fb, nri, typ))
        self.fhdhr.logger.debug("first three bits together : %s" % bt[bc:bc+3])

        if (typ == 7 or typ == 8):
            # this means we have either an SPS or a PPS packet
            # they have the meta-info about resolution, etc.
            # more reading for example here:
            # http://www.cardinalpeak.com/blog/the-h-264-sequence-parameter-set/
            if (typ == 7):
                self.fhdhr.logger.debug("SPS packet")
            else:
                self.fhdhr.logger.debug("PPS packet")
            return startbytes+st[lc:]
            # .. notice here that we include the NAL starting sequence "startbytes" and the "First byte"

        bc += 8
        lc += 1  # let's go to "Second byte"
        # ********* WE ARE AT THE "Second byte" ************
        # The "Type" here is most likely 28, i.e. "FU-A"
        start = bt[bc]  # start bit
        end = bt[bc+2]  # end bit
        nlu1 = bt[bc+3:bc+8]  # 5 nal unit bits

        if (start):  # OK, this is a first fragment in a movie frame
            self.fhdhr.logger.debug("first fragment found")
            nlu = nlu0 + nlu1  # Create "[3 NAL UNIT BITS | 5 NAL UNIT BITS]"
            head = startbytes + nlu.bytes  # .. add the NAL starting sequence
            lc += 1  # We skip the "Second byte"

        if (start is False and end is False):  # intermediate fragment in a sequence, just dump "VIDEO FRAGMENT DATA"
            head = ""
            lc += 1  # We skip the "Second byte"
        elif (end is True):  # last fragment in a sequence, just dump "VIDEO FRAGMENT DATA"
            head = ""
            self.fhdhr.logger.debug("last fragment found")
            lc += 1  # We skip the "Second byte"

        if (typ == 28):  # This code only handles "Type" = 28, i.e. "FU-A"
            return head+st[lc:]
        else:
            self.fhdhr.logger.debug("Unknown frame type")
            return None
