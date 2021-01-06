from gevent.pywsgi import WSGIServer
from flask import Flask, request, session

from .pages import fHDHR_Pages
from .files import fHDHR_Files
from .brython import fHDHR_Brython
from .hdhr import fHDHR_HDHR
from .rmg import fHDHR_RMG
from .api import fHDHR_API


fHDHR_web_VERSION = "v0.8.0-beta"


class fHDHR_HTTP_Server():
    app = None

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

        self.template_folder = fhdhr.config.internal["paths"]["www_templates_dir"]

        self.fhdhr.logger.info("Loading Flask.")

        self.fhdhr.app = Flask("fHDHR", template_folder=self.template_folder)

        # Allow Internal API Usage
        self.fhdhr.app.testing = True
        self.fhdhr.api.client = self.fhdhr.app.test_client()

        # Set Secret Key For Sessions
        self.fhdhr.app.secret_key = self.fhdhr.config.dict["fhdhr"]["friendlyname"]

        self.fhdhr.logger.info("Loading HTTP Pages Endpoints.")
        self.pages = fHDHR_Pages(fhdhr)
        self.add_endpoints(self.pages, "pages")

        self.fhdhr.logger.info("Loading HTTP Files Endpoints.")
        self.files = fHDHR_Files(fhdhr)
        self.add_endpoints(self.files, "files")

        self.fhdhr.logger.info("Loading HTTP Brython Endpoints.")
        self.brython = fHDHR_Brython(fhdhr)
        self.add_endpoints(self.brython, "brython")

        self.fhdhr.logger.info("Loading HTTP HDHR Endpoints.")
        self.hdhr = fHDHR_HDHR(fhdhr)
        self.add_endpoints(self.hdhr, "hdhr")

        self.fhdhr.logger.info("Loading HTTP RMG Endpoints.")
        self.rmg = fHDHR_RMG(fhdhr)
        self.add_endpoints(self.rmg, "rmg")

        self.fhdhr.logger.info("Loading HTTP API Endpoints.")
        self.api = fHDHR_API(fhdhr)
        self.add_endpoints(self.api, "api")

        self.fhdhr.logger.info("Loading HTTP Origin Endpoints.")
        self.origin_endpoints = self.fhdhr.originwrapper.origin.origin_web.fHDHR_Origin_Web(fhdhr)
        self.add_endpoints(self.origin_endpoints, "origin_endpoints")

        self.fhdhr.app.before_request(self.before_request)
        self.fhdhr.app.after_request(self.after_request)
        self.fhdhr.app.before_first_request(self.before_first_request)

    def before_first_request(self):
        self.fhdhr.logger.info("HTTP Server Online.")

    def before_request(self):

        session["is_internal_api"] = self.detect_internal_api(request)
        if session["is_internal_api"]:
            self.fhdhr.logger.debug("Client is using internal API call.")

        session["is_mobile"] = self.detect_mobile(request)
        if session["is_mobile"]:
            self.fhdhr.logger.debug("Client is a mobile device.")

        session["is_plexmediaserver"] = self.detect_plexmediaserver(request)
        if session["is_plexmediaserver"]:
            self.fhdhr.logger.debug("Client is a Plex Media Server.")

        session["deviceauth"] = self.detect_plexmediaserver(request)

        session["tuner_used"] = None

        self.fhdhr.logger.debug("Client %s requested %s Opening" % (request.method, request.path))

    def after_request(self, response):

        # Close Tuner if it was in use, and did not close already
        # if session["tuner_used"] is not None:
        #    tuner = self.fhdhr.device.tuners.tuners[str(session["tuner_used"])]
        #    if tuner.tuner_lock.locked():
        #        self.fhdhr.logger.info("Shutting down Tuner #" + str(session["tuner_used"]) + " after Request.")
        #        tuner.close()

        self.fhdhr.logger.debug("Client %s requested %s Closing" % (request.method, request.path))
        return response

    def detect_internal_api(self, request):
        user_agent = request.headers.get('User-Agent')
        if not user_agent:
            return False
        elif str(user_agent).lower().startswith("fhdhr"):
            return True
        else:
            return False

    def detect_deviceauth(self, request):
        return request.args.get('DeviceAuth', default=None, type=str)

    def detect_mobile(self, request):
        user_agent = request.headers.get('User-Agent')
        phones = ["iphone", "android", "blackberry"]
        if not user_agent:
            return False
        elif any(phone in user_agent.lower() for phone in phones):
            return True
        else:
            return False

    def detect_plexmediaserver(self, request):
        user_agent = request.headers.get('User-Agent')
        if not user_agent:
            return False
        elif str(user_agent).lower().startswith("plexmediaserver"):
            return True
        else:
            return False

    def add_endpoints(self, index_list, index_name):
        item_list = [x for x in dir(index_list) if self.isapath(x)]
        for item in item_list:
            endpoints = eval("self." + str(index_name) + "." + str(item) + ".endpoints")
            if isinstance(endpoints, str):
                endpoints = [endpoints]
            handler = eval("self." + str(index_name) + "." + str(item))
            endpoint_name = eval("self." + str(index_name) + "." + str(item) + ".endpoint_name")
            try:
                endpoint_methods = eval("self." + str(index_name) + "." + str(item) + ".endpoint_methods")
            except AttributeError:
                endpoint_methods = ['GET']
            self.fhdhr.logger.debug("Adding endpoint %s available at %s with %s methods." % (endpoint_name, ",".join(endpoints), ",".join(endpoint_methods)))
            for endpoint in endpoints:
                self.add_endpoint(endpoint=endpoint,
                                  endpoint_name=endpoint_name,
                                  handler=handler,
                                  methods=endpoint_methods)

    def isapath(self, item):
        not_a_page_list = ["fhdhr"]
        if item in not_a_page_list:
            return False
        elif item.startswith("__") and item.endswith("__"):
            return False
        else:
            return True

    def add_endpoint(self, endpoint=None, endpoint_name=None, handler=None, methods=['GET']):
        self.fhdhr.app.add_url_rule(endpoint, endpoint_name, handler, methods=methods)

    def run(self):

        self.http = WSGIServer(self.fhdhr.api.address_tuple,
                               self.fhdhr.app.wsgi_app,
                               log=self.fhdhr.logger)

        try:
            self.http.serve_forever()
        except KeyboardInterrupt:
            self.http.stop()
