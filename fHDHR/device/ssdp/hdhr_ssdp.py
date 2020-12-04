

class HDHR_SSDP():

    def __init__(self, fhdhr, _broadcast_ip):
        self.fhdhr = fhdhr

        self.ssdp_content = None

        self._broadcast_ip = _broadcast_ip
        self.nt = 'urn:schemas-upnp-org:device:MediaServer:1'
        self.usn = 'uuid:' + fhdhr.config.dict["main"]["uuid"] + '::' + self.nt
        self.server = 'fHDHR/%s UPnP/1.0' % fhdhr.version
        self.location = ('http://' + fhdhr.config.dict["fhdhr"]["discovery_address"] + ':' +
                         str(fhdhr.config.dict["fhdhr"]["port"]) + '/device.xml')
        self.al = self.location
        self.max_age = 1800

    def get(self):
        if self.ssdp_content:
            return self.ssdp_content.encode("utf-8")

        data = (
            "NOTIFY * HTTP/1.1\r\n"
            "HOST:{}\r\n"
            "NT:{}\r\n"
            "NTS:ssdp:alive\r\n"
            "USN:{}\r\n"
            "SERVER:{}\r\n"
        ).format(
                 self._broadcast_ip,
                 self.nt,
                 self.usn,
                 self.server
                 )
        if self.location is not None:
            data += "LOCATION:{}\r\n".format(self.location)
        if self.al is not None:
            data += "AL:{}\r\n".format(self.al)
        if self.max_age is not None:
            data += "Cache-Control:max-age={}\r\n".format(self.max_age)
        data += "\r\n"
        self.ssdp_content = data
        return data.encode("utf-8")
