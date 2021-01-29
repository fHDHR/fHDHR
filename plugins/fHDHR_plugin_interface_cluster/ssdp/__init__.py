
class fHDHR_Detect():

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr
        self.fhdhr.db.delete_fhdhr_value("ssdp_detect", "list")

    def set(self, location):
        detect_list = self.fhdhr.db.get_fhdhr_value("ssdp_detect", "list") or []
        if location not in detect_list:
            detect_list.append(location)
            self.fhdhr.db.set_fhdhr_value("ssdp_detect", "list", detect_list)

    def get(self):
        return self.fhdhr.db.get_fhdhr_value("ssdp_detect", "list") or []


class Plugin_OBJ():

    def __init__(self, fhdhr, plugin_utils, broadcast_ip, max_age):
        self.fhdhr = fhdhr

        self.detect_method = fHDHR_Detect(fhdhr)

        self.broadcast_ip = broadcast_ip
        self.device_xml_path = '/cluster/device.xml'
        self.schema = "upnp:rootdevice"

        self.max_age = max_age

    @property
    def enabled(self):
        return self.fhdhr.config.dict["cluster"]["enabled"]

    @property
    def notify(self):

        data = ''
        data_command = "NOTIFY * HTTP/1.1"

        data_dict = {
                    "HOST": "%s:%d" % ("239.255.255.250", 1900),
                    "NTS": "ssdp:alive",
                    "USN": 'uuid:%s::%s' % (self.fhdhr.config.dict["main"]["uuid"], self.schema),
                    "LOCATION": "%s%s" % (self.fhdhr.api.base, self.device_xml_path),
                    "EXT": '',
                    "SERVER": 'fHDHR/%s UPnP/1.0' % self.fhdhr.version,
                    "Cache-Control:max-age=": self.max_age,
                    "NT": self.schema,
                    }

        data += "%s\r\n" % data_command
        for data_key in list(data_dict.keys()):
            data += "%s:%s\r\n" % (data_key, data_dict[data_key])
        data += "\r\n"

        return data

    def on_recv(self, headers, cmd, ssdp_handling):
        if cmd[0] == 'NOTIFY' and cmd[1] == '*':
            try:
                if headers["server"].startswith("fHDHR"):
                    if headers["location"].endswith("/device.xml"):
                        savelocation = headers["location"].split("/device.xml")[0]
                        if savelocation.endswith("/cluster"):
                            savelocation = savelocation.replace("/cluster", '')
                            if savelocation != self.fhdhr.api.base:
                                self.detect_method.set(savelocation)
            except KeyError:
                return
