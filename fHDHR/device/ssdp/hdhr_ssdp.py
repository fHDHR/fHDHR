

class HDHR_SSDP():

    def __init__(self, fhdhr, broadcast_ip, max_age):
        self.fhdhr = fhdhr

        self.ssdp_content = None

        self.broadcast_ip = broadcast_ip
        self.device_xml_path = '/device.xml'

        self.max_age = max_age

    def get(self):
        if self.ssdp_content:
            return self.ssdp_content.encode("utf-8")

        data = ''
        data_command = "NOTIFY * HTTP/1.1"

        data_dict = {
                    "HOST": "%s:%s" % (self.broadcast_ip, 1900),
                    "NT": 'urn:schemas-upnp-org:device:MediaServer:1',
                    "NTS": "ssdp:alive",
                    "USN": 'uuid:%s::%s' % (self.fhdhr.config.dict["main"]["uuid"], 'urn:schemas-upnp-org:device:MediaServer:1'),
                    "SERVER": 'fHDHR/%s UPnP/1.0' % self.fhdhr.version,
                    "LOCATION": "%s%s" % (self.fhdhr.api.base, self.device_xml_path),
                    "AL": "%s%s" % (self.fhdhr.api.base, self.device_xml_path),
                    "Cache-Control:max-age=": self.max_age
                    }

        data += "%s\r\n" % data_command
        for data_key in list(data_dict.keys()):
            data += "%s:%s\r\n" % (data_key, data_dict[data_key])
        data += "\r\n"

        self.ssdp_content = data
        return data.encode("utf-8")
