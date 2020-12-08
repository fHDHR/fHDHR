import urllib.parse


class fHDHR_API_URLs():

    def __init__(self, settings):
        self.config = settings

        self.address = self.config.dict["fhdhr"]["address"]
        self.discovery_address = self.config.dict["fhdhr"]["discovery_address"]
        self.port = self.config.dict["fhdhr"]["port"]

    @property
    def base(self):
        if self.discovery_address:
            return ('http://%s:%s' % self.discovery_address_tuple)
        elif self.address == "0.0.0.0":
            return ('http://%s:%s' % self.address_tuple)
        else:
            return ('http://%s:%s' % self.address_tuple)

    @property
    def base_quoted(self):
        return urllib.parse.quote(self.base)

    @property
    def discovery_address_tuple(self):
        return (self.discovery_address, int(self.port))

    @property
    def localhost_address_tuple(self):
        return ("127.0.0.1", int(self.port))

    @property
    def address_tuple(self):
        return (self.address, int(self.port))
