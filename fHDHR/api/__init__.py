import urllib.parse


class Fillin_Client():

    def __init__(self, settings, web):
        self.config = settings
        self.web = web

    def __getattr__(self, name):
        ''' will only get called for undefined attributes '''
        if hasattr(self.web.session, name):
            return eval("self.web.session.%s" % name)


class fHDHR_API_URLs():

    def __init__(self, settings, web, versions):
        self.config = settings
        self.web = web
        self.versions = versions

        self.headers = {'User-Agent': "fHDHR/%s" % self.versions.dict["fHDHR"]}

        # Replaced later
        self.client = Fillin_Client(settings, web)

    @property
    def address(self):
        return self.config.dict["fhdhr"]["address"]

    @property
    def discovery_address(self):
        return self.config.dict["fhdhr"]["discovery_address"]

    @property
    def multicast_address(self):
        return self.config.dict["ssdp"]["multicast_address"]

    @property
    def port(self):
        return self.config.dict["fhdhr"]["port"]

    def get(self, url, *args):

        req_method = type(self.client).__name__

        if not url.startswith("http"):
            if not url.startswith("/"):
                url = "/%s" % url
            url = "%s%s" % (self.base, url)

        if req_method == "FlaskClient":
            self.client.get(url, headers=self.headers, *args)
        else:
            self.client.get(url, headers=self.headers, *args)

    def post(self, url, *args):

        req_method = type(self.client).__name__

        if not url.startswith("http"):
            if not url.startswith("/"):
                url = "/%s" % url
            url = "%s%s" % (self.base, url)

        if req_method == "FlaskClient":
            self.client.post(url, headers=self.headers, *args)
        else:
            self.client.post(url, headers=self.headers, *args)

    @property
    def base(self):
        if self.discovery_address:
            return ('http://%s:%s' % self.discovery_address_tuple)
        elif self.multicast_address:
            return ('http://%s:%s' % self.multicast_address_tuple)
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
    def multicast_address_tuple(self):
        return (self.multicast_address, int(self.port))

    @property
    def localhost_address_tuple(self):
        return ("127.0.0.1", int(self.port))

    @property
    def address_tuple(self):
        return (self.address, int(self.port))
