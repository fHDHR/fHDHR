# Adapted from https://github.com/MoshiBin/ssdpy and https://github.com/ZeWaren/python-upnp-ssdp-example
import socket
import struct
import time
import threading

from .ssdp_detect import fHDHR_Detect
from .rmg_ssdp import RMG_SSDP
from .hdhr_ssdp import HDHR_SSDP


class SSDPServer():

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

        self.detect_method = fHDHR_Detect(fhdhr)

        self.fhdhr.threads["ssdp"] = threading.Thread(target=self.run)

        if (self.fhdhr.config.dict["fhdhr"]["discovery_address"] and
           self.fhdhr.config.dict["ssdp"]["enabled"]):
            self.setup_ssdp()

            self.sock.bind((self.bind_address, 1900))

            self.msearch_payload = self.create_msearch_payload()

            self.max_age = int(fhdhr.config.dict["ssdp"]["max_age"])
            self.age_time = None

            self.rmg_ssdp = RMG_SSDP(fhdhr, self.broadcast_ip, self.max_age)
            self.hdhr_ssdp = HDHR_SSDP(fhdhr, self.broadcast_ip, self.max_age)

            self.do_alive()
            self.m_search()

    def start(self):
        self.fhdhr.logger.info("SSDP Server Starting")
        self.fhdhr.threads["ssdp"].start()

    def stop(self):
        self.fhdhr.logger.info("SSDP Server Stopping")
        self.sock.close()

    def run(self):
        while True:
            data, address = self.sock.recvfrom(1024)
            self.on_recv(data, address)
            self.do_alive()
        self.stop()

    def do_alive(self, forcealive=False):

        send_alive = False
        if not self.age_time:
            send_alive = True
        elif forcealive:
            send_alive = True
        elif time.time() >= (self.age_time + self.max_age):
            send_alive = True

        if send_alive:
            self.fhdhr.logger.info("Sending Alive message to network.")
            self.do_notify(self.broadcase_address_tuple)
            self.age_time = time.time()

    def do_notify(self, address):

        notify_list = []

        hdhr_notify = self.hdhr_ssdp.get()
        notify_list.append(hdhr_notify)

        if self.fhdhr.config.dict["rmg"]["enabled"]:
            rmg_notify = self.rmg_ssdp.get()
            notify_list.append(rmg_notify)

        for notifydata in notify_list:

            self.fhdhr.logger.debug("Created {}".format(notifydata))
            try:
                self.sock.sendto(notifydata, address)
            except OSError as e:
                # Most commonly: We received a multicast from an IP not in our subnet
                self.fhdhr.logger.debug("Unable to send NOTIFY: %s" % e)
                pass

    def on_recv(self, data, address):
        self.fhdhr.logger.debug("Received packet from {}: {}".format(address, data))

        try:
            header, payload = data.decode().split('\r\n\r\n')[:2]
        except ValueError:
            self.fhdhr.logger.error("Error with Received packet from {}: {}".format(address, data))
            return

        lines = header.split('\r\n')
        cmd = lines[0].split(' ')
        lines = map(lambda x: x.replace(': ', ':', 1), lines[1:])
        lines = filter(lambda x: len(x) > 0, lines)

        headers = [x.split(':', 1) for x in lines]
        headers = dict(map(lambda x: (x[0].lower(), x[1]), headers))

        if cmd[0] == 'M-SEARCH' and cmd[1] == '*':
            # SSDP discovery
            self.fhdhr.logger.debug("Received qualifying M-SEARCH from {}".format(address))
            self.fhdhr.logger.debug("M-SEARCH data: {}".format(headers))

            self.do_notify(address)

        elif cmd[0] == 'NOTIFY' and cmd[1] == '*':
            # SSDP presence
            self.fhdhr.logger.debug("NOTIFY data: {}".format(headers))
            try:
                if headers["server"].startswith("fHDHR"):
                    savelocation = headers["location"].split("/device.xml")[0]
                    if savelocation.endswith("/hdhr"):
                        savelocation = savelocation.replace("/hdhr", '')
                    elif savelocation.endswith("/rmg"):
                        savelocation = savelocation.replace("/rmg", '')
                    if savelocation != self.fhdhr.api.base:
                        self.detect_method.set(savelocation)
            except KeyError:
                return
        else:
            self.fhdhr.logger.debug('Unknown SSDP command %s %s' % (cmd[0], cmd[1]))

    def m_search(self):
        data = self.msearch_payload
        self.sock.sendto(data, self.broadcase_address_tuple)

    def create_msearch_payload(self):

        data = ''
        data_command = "M-SEARCH * HTTP/1.1"

        data_dict = {
                    "HOST": "%s:%s" % (self.broadcast_ip, 1900),
                    "MAN": "ssdp:discover",
                    "ST": "ssdp:all",
                    "MX": 1,
                    }

        data += "%s\r\n" % data_command
        for data_key in list(data_dict.keys()):
            data += "%s:%s\r\n" % (data_key, data_dict[data_key])
        data += "\r\n"

        return data.encode("utf-8")

    def setup_ssdp(self):
        self.sock = None

        self.proto = self.setup_proto()
        self.iface = self.fhdhr.config.dict["ssdp"]["iface"]
        self.address = self.fhdhr.config.dict["ssdp"]["multicast_address"]
        self.setup_addressing()

        self.sock = socket.socket(self.af_type, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.setup_interface()

        self.setup_multicasting()

    def setup_proto(self):
        proto = self.fhdhr.config.dict["ssdp"]["proto"]
        allowed_protos = ("ipv4", "ipv6")
        if proto not in allowed_protos:
            raise ValueError("Invalid proto - expected one of {}".format(allowed_protos))
        return proto

    def setup_addressing(self):
        if self.proto == "ipv4":
            self.af_type = socket.AF_INET
            self.broadcast_ip = "239.255.255.250"
            self.broadcase_address_tuple = (self.broadcast_ip, 1900)
            self.bind_address = "0.0.0.0"
        elif self.proto == "ipv6":
            self.af_type = socket.AF_INET6
            self.broadcast_ip = "ff02::c"
            self.broadcast_address_tuple = (self.broadcast_ip, 1900, 0, 0)
            self.bind_address = "::"

    def setup_interface(self):
        # Bind to specific interface
        if self.iface is not None:
            self.sock.setsockopt(socket.SOL_SOCKET, getattr(socket, "SO_BINDTODEVICE", 25), self.iface)

    def setup_multicasting(self):
        # Subscribe to multicast address
        if self.proto == "ipv4":
            mreq = socket.inet_aton(self.broadcast_ip)
            if self.address is not None:
                mreq += socket.inet_aton(self.address)
            else:
                mreq += struct.pack(b"@I", socket.INADDR_ANY)
            self.sock.setsockopt(
                socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            # Allow multicasts on loopback devices (necessary for testing)
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
        elif self.proto == "ipv6":
            # In IPv6 we use the interface index, not the address when subscribing to the group
            mreq = socket.inet_pton(socket.AF_INET6, self.broadcast_ip)
            if self.iface is not None:
                iface_index = socket.if_nametoindex(self.iface)
                # Send outgoing packets from the same interface
                self.sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_IF, iface_index)
                mreq += struct.pack(b"@I", iface_index)
            else:
                mreq += socket.inet_pton(socket.AF_INET6, "::")
            self.sock.setsockopt(
                socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mreq,
            )
            self.sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, 1)
