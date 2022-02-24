# Adapted from https://github.com/MoshiBin/ssdpy and https://github.com/ZeWaren/python-upnp-ssdp-example
import socket
import struct
import threading

import fHDHR.exceptions


class SSDPServer():
    """
    fHDHR SSDP server.
    """

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

        # Gather Default settings to pass to ssdp plugins later
        self.default_settings = {
            }

        # Create Default Config Values and Descriptions for ssdp plugins
        self.default_settings = self.fhdhr.config.get_plugin_defaults(self.default_settings)

        self.ssdp_handling = {}

        if self.multicast_address and self.fhdhr.config.dict["ssdp"]["enabled"] and len(self.methods):

            self.fhdhr.logger.info("Initializing SSDP system")

            try:
                self.setup_ssdp()
                self.sock.bind((self.bind_address, 1900))

                self.msearch_payload = self.create_msearch_payload()

                self.max_age = int(fhdhr.config.dict["ssdp"]["max_age"])
                self.age_time = None

                self.ssdp_doalive_url = "/api/ssdp?method=alive"

                if self.max_age:
                    self.fhdhr.scheduler.every(self.max_age).seconds.do(
                        self.fhdhr.scheduler.job_wrapper(self.do_alive)).tag("SSDP Alive")

                self.ssdp_method_selfadd()

                self.m_search()

                self.fhdhr.threads["ssdp"] = threading.Thread(target=self.run)

            except OSError as err:
                self.fhdhr.logger.Error("SSDP system will not be Initialized: %s" % err)

        elif not self.fhdhr.config.dict["ssdp"]["enabled"]:
            self.fhdhr.logger.info("SSDP system will not be Initialized: Not Enabled")
        elif not self.multicast_address:
            self.fhdhr.logger.info("SSDP system will not be Initialized: Address not set in [ssdp]multicast_address or [fhdhr]discovery_address")
        elif not len(self.methods):
            self.fhdhr.logger.info("SSDP system will not be Initialized: No SSDP Plugins installed.")
        else:
            self.fhdhr.logger.info("SSDP system will not be Initialized")

    @property
    def methods(self):
        return self.fhdhr.plugins.search_by_type("ssdp")

    def ssdp_method_selfadd(self):
        """
        Add SSDP methods.
        """

        self.fhdhr.logger.info("Detecting and Opening any found SSDP plugins.")
        for plugin_name in self.fhdhr.plugins.search_by_type("ssdp"):
            method = self.fhdhr.plugins.plugins[plugin_name].name.lower()
            plugin_utils = self.fhdhr.plugins.plugins[plugin_name].plugin_utils

            try:
                self.ssdp_handling[method] = self.fhdhr.plugins.plugins[plugin_name].Plugin_OBJ(self.fhdhr, plugin_utils, self.broadcast_ip, self.max_age)
                self.fhdhr.logger.info("Added plugin %s, method %s" % (plugin_name, method))

            except fHDHR.exceptions.SSDPSetupError as e:
                self.fhdhr.logger.error(e)

            except Exception as e:
                self.fhdhr.logger.error(e)

            # Set config defaults for method
            self.fhdhr.config.set_plugin_defaults(method, self.default_settings)

            for default_setting in list(self.default_settings.keys()):

                # Set ssdp plugin attributes if missing
                if not hasattr(self.ssdp_handling[method], default_setting):
                    self.fhdhr.logger.debug("Setting %s %s attribute to: %s" % (method, default_setting, self.fhdhr.config.dict[method][default_setting]))
                    setattr(self.ssdp_handling[method], default_setting, self.fhdhr.config.dict[method][default_setting])

    def start(self):
        """
        Start SSDP.
        """

        self.fhdhr.logger.info("SSDP Server Starting")
        self.fhdhr.threads["ssdp"].start()
        self.fhdhr.logger.debug("SSDP Server Started")

    def stop(self):
        """
        Safely Shutdown SSDP.
        """

        self.fhdhr.logger.info("SSDP Server Stopping")
        self.sock.close()
        self.fhdhr.logger.debug("SSDP Server Stopped")

    def run(self):
        """
        Listen for SSDP Requests.
        """

        while True:
            data, address = self.sock.recvfrom(1024)
            self.on_recv(data, address)
        self.stop()

    def do_alive(self):
        """
        Notify Network of SSDP.
        """

        if self.broadcast_address_tuple:
            self.fhdhr.logger.info("Sending Alive message to network.")
            self.do_notify(self.broadcast_address_tuple)

    def do_notify(self, address):
        """
        Notify Network of SSDP.
        """

        notify_list = []
        for ssdp_handler in list(self.ssdp_handling.keys()):
            if self.ssdp_handling[ssdp_handler].enabled and hasattr(self.ssdp_handling[ssdp_handler], 'notify'):
                notify_data = self.ssdp_handling[ssdp_handler].notify
                if isinstance(notify_data, list):
                    notify_list.extend(notify_data)
                else:
                    notify_list.append(notify_data)

        for notifydata in notify_list:
            notifydata = notifydata.encode("utf-8")

            self.fhdhr.logger.ssdp("Created {}".format(notifydata))
            try:
                self.sock.sendto(notifydata, address)
            except OSError as e:
                # Most commonly: We received a multicast from an IP not in our subnet
                self.fhdhr.logger.ssdp("Unable to send NOTIFY: %s" % e)
                pass

    def on_recv(self, data, address):
        """
        Handle Reqeusts for SSDP information.
        """

        self.fhdhr.logger.ssdp("Received packet from {}: {}".format(address, data))

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

        for ssdp_handler in list(self.ssdp_handling.keys()):
            if self.ssdp_handling[ssdp_handler].enabled and hasattr(self.ssdp_handling[ssdp_handler], 'on_recv'):
                self.ssdp_handling[ssdp_handler].on_recv(headers, cmd, list(self.ssdp_handling.keys()))

        if cmd[0] == 'M-SEARCH' and cmd[1] == '*':
            # SSDP discovery
            self.fhdhr.logger.ssdp("Received qualifying M-SEARCH from {}".format(address))
            self.fhdhr.logger.ssdp("M-SEARCH data: {}".format(headers))

            self.do_notify(address)

        if cmd[0] == 'NOTIFY' and cmd[1] == '*':
            self.fhdhr.logger.ssdp("NOTIFY data: {}".format(headers))
        else:
            self.fhdhr.logger.ssdp('Unknown SSDP command %s %s' % (cmd[0], cmd[1]))

    def m_search(self):
        """
        Search Network for SSDP
        """

        data = self.msearch_payload
        if self.broadcast_address_tuple:
            self.sock.sendto(data, self.broadcast_address_tuple)

    def create_msearch_payload(self):
        """
        Create Payload for searching network.
        """

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

    @property
    def multicast_address(self):
        """
        The Address for multicast to listen.
        """

        if self.fhdhr.config.dict["ssdp"]["multicast_address"]:
            return self.fhdhr.config.dict["ssdp"]["multicast_address"]

        elif self.fhdhr.config.dict["fhdhr"]["discovery_address"]:
            return self.fhdhr.config.dict["fhdhr"]["discovery_address"]

        return None

    def setup_ssdp(self):
        """
        Setup SSDP basics.
        """

        self.sock = None

        self.proto = self.setup_proto()
        self.iface = self.fhdhr.config.dict["ssdp"]["iface"]
        self.setup_addressing()

        self.sock = socket.socket(self.af_type, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.setup_interface()

        self.setup_multicasting()

    def setup_proto(self):
        """
        Setup SSDP protocols.
        """

        proto = self.fhdhr.config.dict["ssdp"]["proto"]
        allowed_protos = ("ipv4", "ipv6")

        if proto not in allowed_protos:
            raise ValueError("Invalid proto - expected one of {}".format(allowed_protos))

        return proto

    def setup_addressing(self):
        """
        Setup SSDP addressing.
        """

        if self.proto == "ipv4":
            self.af_type = socket.AF_INET
            self.broadcast_ip = "239.255.255.250"
            self.broadcast_address_tuple = (self.broadcast_ip, 1900)
            self.bind_address = "0.0.0.0"

        elif self.proto == "ipv6":
            self.af_type = socket.AF_INET6
            self.broadcast_ip = "ff02::c"
            self.broadcast_address_tuple = (self.broadcast_ip, 1900, 0, 0)
            self.bind_address = "::"

        else:
            self.broadcast_address_tuple = None

    def setup_interface(self):
        """
        Setup SSDP interface.
        """

        # Bind to specific interface
        if self.iface is not None:
            self.sock.setsockopt(socket.SOL_SOCKET, getattr(socket, "SO_BINDTODEVICE", 25), self.iface)

    def setup_multicasting(self):
        """
        Setup SSDP multicasting.
        """

        # Subscribe to multicast address
        if self.proto == "ipv4":

            mreq = socket.inet_aton(self.broadcast_ip)
            if self.multicast_address is not None:
                mreq += socket.inet_aton(self.multicast_address)

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
