

class Plugin_OBJ():

    def __init__(self, fhdhr, plugin_utils, broadcast_ip, max_age):
        self.fhdhr = fhdhr

        self.broadcast_ip = broadcast_ip

        self.schema = "urn:plex-tv:service:MediaGrabber:1"

        self.max_age = max_age

    def create_ssdp_content(self, origin):
        data = ''
        data_command = "NOTIFY * HTTP/1.1"

        device_xml_path = "/rmg/%s%s/device.xml" % (self.fhdhr.config.dict["main"]["uuid"], origin)

        data_dict = {
                    "HOST": "%s:%s" % ("239.255.255.250", 1900),
                    "NT": self.schema,
                    "NTS": "ssdp:alive",
                    "USN": 'uuid:%s%s::%s' % (self.fhdhr.config.dict["main"]["uuid"], origin, self.schema),
                    "SERVER": 'fHDHR/%s UPnP/1.0' % self.fhdhr.version,
                    "LOCATION": "%s%s" % (self.fhdhr.api.base, device_xml_path),
                    "AL": "%s%s" % (self.fhdhr.api.base, device_xml_path),
                    "Cache-Control:max-age=": self.max_age
                    }

        data += "%s\r\n" % data_command
        for data_key in list(data_dict.keys()):
            data += "%s:%s\r\n" % (data_key, data_dict[data_key])
        data += "\r\n"

        self.ssdp_content = data
        return data

    @property
    def enabled(self):
        return self.fhdhr.config.dict["rmg"]["enabled"]

    @property
    def notify(self):
        ssdp_content = []
        for origin in list(self.ssdp_content.keys()):
            data = self.create_ssdp_content(origin)
            ssdp_content.append(data)
        return ssdp_content
