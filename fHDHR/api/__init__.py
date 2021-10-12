import urllib.parse
import threading


class Fillin_Client():
    """
    Until fHDHR_web is loaded, use requests for internal API calls.
    """

    def __init__(self, settings, web):
        self.config = settings
        self.web = web

    def __getattr__(self, name):
        """
        Quick and dirty shortcuts. Will only get called for undefined attributes.
        """

        if hasattr(self.web.session, name):
            return eval("self.web.session.%s" % name)


class fHDHR_API_URLs():
    """
    Methods for calling the fHDHR_web internally.
    """

    def __init__(self, settings, web, versions, logger):
        self.config = settings
        self.web = web
        self.versions = versions
        self.logger = logger

        self.headers = {'User-Agent': "fHDHR/%s" % self.versions.dict["fHDHR"]}

        self.fillinclient = Fillin_Client(settings, web)
        # Replaced later
        self.client = self.fillinclient

    @property
    def address(self):
        """
        A reference to the address fHDHR is set to run on.
        """

        return self.config.dict["fhdhr"]["address"]

    @property
    def discovery_address(self):
        """
        A reference to the discovery address fHDHR is set to run on.
        """

        return self.config.dict["fhdhr"]["discovery_address"]

    @property
    def multicast_address(self):
        """
        A reference to the SSDP multicast address fHDHR is set to run on.
        """

        return self.config.dict["ssdp"]["multicast_address"]

    @property
    def port(self):
        """
        A reference to the port fHDHR is set to run on.
        """

        return self.config.dict["fhdhr"]["port"]

    def no_response_get(self, url, *args):
        """
        A method to simulate a GET request to the fHDHR_web API internally, but without waiting for a response.
        """
        self.logger.debug("Using a GET request to %s without waiting for a response" % url)

        if not url.startswith("http"):

            if not url.startswith("/"):
                url = "/%s" % url

            url = "%s%s" % (self.base, url)

        try:
            self.fillinclient.get(url, headers=self.headers, timeout=0.0000000001, *args)
        except self.fillinclient.exceptions.ReadTimeout:
            pass

    def no_response_post(self, url, *args):
        """
        A method to simulate a POST request to the fHDHR_web API internally, but without waiting for a response.
        """
        self.logger.debug("Using a GET request to %s without waiting for a response" % url)

        if not url.startswith("http"):

            if not url.startswith("/"):
                url = "/%s" % url

            url = "%s%s" % (self.base, url)

        try:
            self.fillinclient.post(url, headers=self.headers, timeout=0.0000000001, *args)
        except self.fillinclient.exceptions.ReadTimeout:
            pass

    def threadget(self, url, *args):
        """
        A method to simulate a GET request to the fHDHR_web API internally, but in a seperate thread.
        """

        self.logger.debug("Starting a thread to simulate a GET request to %s" % url)
        api_get = threading.Thread(target=self.get, args=(url, *args,))
        api_get.start()

    def threadpost(self, url, *args):
        """
        A method to simulate a POST request to the fHDHR_web API internally, but in a seperate thread.
        """

        self.logger.debug("Starting a thread to simulate a POST request to %s" % url)
        api_post = threading.Thread(target=self.post, args=(url, *args,))
        api_post.start()

    def get(self, url, *args):
        """
        A method to simulate a GET request to the fHDHR_web API internally.
        """

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
        """
        A method to simulate a POST request to the fHDHR_web API internally.
        """

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
        """
        Find the best possible base address to trigger internal API with.
        """

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
        """
        The base address suited for a url parameter.
        """

        return urllib.parse.quote(self.base)

    @property
    def discovery_address_tuple(self):
        """
        A tuple of the discovery address and the port set for fHDHR.
        """

        return (self.discovery_address, int(self.port))

    @property
    def multicast_address_tuple(self):
        """
        A tuple of the multicast address and the port set for fHDHR.
        """

        return (self.multicast_address, int(self.port))

    @property
    def localhost_address_tuple(self):
        """
        A tuple of the localhost address and the port.
        """

        return ("127.0.0.1", int(self.port))

    @property
    def address_tuple(self):
        """
        A tuple of the address and the port set for fHDHR.
        """

        return (self.address, int(self.port))
