from gevent.pywsgi import WSGIServer
from flask import Flask, request, session
import threading
import uuid

from .pages import fHDHR_Pages
from .files import fHDHR_Files
from .brython import fHDHR_Brython
from .api import fHDHR_API

from .webplugin import WebPlugin
from fHDHR.tools import checkattr


class fHDHR_HTTP_Server():
    """
    fHDHR_web HTTP Frontend.
    """

    app = None

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

        self.template_folder = fhdhr.config.internal["paths"]["www_templates_dir"]

        # Create list of pages to refresh
        self.refresh_pages = self.fhdhr.config.dict["web_ui"]["pages_to_refresh"] or []
        if isinstance(self.refresh_pages, str):
            self.refresh_pages = [self.refresh_pages]

        self.fhdhr.logger.info("Loading Flask.")

        self.fhdhr.app = Flask("fHDHR", template_folder=self.template_folder)
        self.instance_id = str(uuid.uuid4())

        # Allow Internal API Usage
        self.fhdhr.app.testing = True
        self.fhdhr.api.client = self.fhdhr.app.test_client()

        # Set Secret Key For Sessions
        self.fhdhr.app.secret_key = self.fhdhr.config.dict["fhdhr"]["friendlyname"]

        self.route_list = {}

        self.endpoints_dict = {}
        self.endpoints_dict["brython"] = fHDHR_Brython(fhdhr)
        self.endpoints_dict["api"] = fHDHR_API(fhdhr)

        # Load Plugins before pages so they can override core web pages
        self.selfadd_plugins()

        self.endpoints_dict["pages"] = fHDHR_Pages(fhdhr)
        self.endpoints_dict["files"] = fHDHR_Files(fhdhr)

        for endpoint_type in list(self.endpoints_dict.keys()):
            self.fhdhr.logger.info("Loading HTTP %s Endpoints." % endpoint_type)
            self.add_endpoints(endpoint_type)

        # self.fhdhr.app.before_first_request(self.before_first_request)  # deprecated
        # self.before_first_request_triggered = False
        # self.fhdhr.app.before_request_funcs = ([(None, self.before_first_request())])

        self.fhdhr.app.before_request(self.before_request)
        self.fhdhr.app.after_request(self.after_request)

        self.fhdhr.threads["flask"] = threading.Thread(target=self.run)

    def selfadd_plugins(self):
        """
        Import web Plugins.
        """

        for plugin_name in self.fhdhr.plugins.search_by_type("web"):

            plugin = self.fhdhr.plugins.plugins[plugin_name]
            method = plugin.name.lower()
            self.fhdhr.logger.info("Found Web Plugin: %s" % method)
            self.endpoints_dict[method] = WebPlugin(self.fhdhr, plugin)

            if method in list(self.endpoints_dict.keys()):

                # Extend Refresh Page list
                pages_to_refresh = self.endpoints_dict[method].pages_to_refresh
                self.refresh_pages.extend(pages_to_refresh)

    def start(self):
        """
        Start Flask.
        """

        self.fhdhr.logger.info("Flask HTTP Thread Starting")
        self.fhdhr.threads["flask"].start()

    def stop(self):
        """
        Safely Stop Flask.
        """

        self.fhdhr.logger.info("Flask HTTP Thread Stopping")
        self.http.stop()

    def before_first_request(self):
        """
        Handling before a first request can be handled.
        """

        if not self.before_first_request_triggered:
            self.tdarr_inform.logger.info("HTTP Server Online.")
            self.before_first_request_triggered = True

    def before_request(self):
        """
        Handling before a request is processed.
        """

        session["session_id"] = str(uuid.uuid4())
        session["instance_id"] = self.instance_id
        session["route_list"] = self.route_list
        session["refresh_pages"] = self.refresh_pages
        try:
            session["endpoint_name"] = str(request.url_rule.endpoint)
        except AttributeError:
            session["endpoint_name"] = None

        session["user_agent"] = request.headers.get('User-Agent')

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

        session["restart"] = False

        self.fhdhr.logger.debug("Client %s requested %s Opening" % (request.method, request.path))

    def after_request(self, response):
        """
        Handling after a request is processed.
        """

        # Close Tuner if it was in use, and did not close already
        # if session["tuner_used"] is not None:
        #    tuner = self.fhdhr.device.tuners.tuners[str(session["tuner_used"])]
        #    if tuner.tuner_lock.locked():
        #        self.fhdhr.logger.info("Shutting down Tuner #%s after Request." % session["tuner_used"])
        #        tuner.close()

        self.fhdhr.logger.debug("Client %s requested %s Closing" % (request.method, request.path))

        if not session["restart"]:
            return response

        else:
            return self.stop()

    def detect_internal_api(self, request):
        """
        Detect if accessed by internal API.
        """

        user_agent = request.headers.get('User-Agent')
        if not user_agent:
            return False
        elif str(user_agent).lower().startswith("fhdhr"):
            return True
        else:
            return False

    def detect_deviceauth(self, request):
        """
        Detect if accessed with DeviceAuth.
        """

        return request.args.get('DeviceAuth', default=None, type=str)

    def detect_mobile(self, request):
        """
        Detect if accessed by mobile.
        """

        user_agent = request.headers.get('User-Agent')
        phones = ["iphone", "android", "blackberry"]

        if not user_agent:
            return False

        elif any(phone in user_agent.lower() for phone in phones):
            return True

        else:
            return False

    def detect_plexmediaserver(self, request):
        """
        Detect if accessed by plexmediaserver.
        """

        user_agent = request.headers.get('User-Agent')

        if not user_agent:
            return False

        elif str(user_agent).lower().startswith("plexmediaserver"):
            return True

        else:
            return False

    def add_endpoints(self, index_name):
        """
        Add Endpoints.
        """

        endpoint_obj = self.endpoints_dict[index_name]

        if type(endpoint_obj).__name__ == "WebPlugin":
            item_list = [x for x in endpoint_obj.endpoint_directory if self.isapath(x)]
        else:
            item_list = [x for x in dir(endpoint_obj) if self.isapath(x)]

        for item in item_list:

            endpoint_handler = eval("endpoint_obj.%s" % item)

            if checkattr(endpoint_handler, "endpoints"):
                endpoints = endpoint_handler.endpoints
                if isinstance(endpoints, str):
                    endpoints = [endpoints]
            else:
                endpoints = [str(type(endpoint_handler).__name__)]

            if checkattr(endpoint_handler, "endpoint_name"):
                endpoint_name = endpoint_handler.endpoint_name
            else:
                endpoint_name = type(endpoint_handler).__name__

            if checkattr(endpoint_handler, "endpoint_methods"):
                endpoint_methods = endpoint_handler.endpoint_methods
            else:
                endpoint_methods = ['GET']

            if checkattr(endpoint_handler, "endpoint_access_level"):
                endpoint_access_level = endpoint_handler.endpoint_access_level
            else:
                endpoint_access_level = 0

            if checkattr(endpoint_handler, "pretty_name"):
                pretty_name = endpoint_handler.pretty_name
            else:
                pretty_name = endpoint_name

            if checkattr(endpoint_handler, "endpoint_category"):
                endpoint_category = endpoint_handler.endpoint_category
            else:
                endpoint_category = index_name

            if checkattr(endpoint_handler, "endpoint_parameters"):
                endpoint_parameters = endpoint_handler.endpoint_parameters
            else:
                endpoint_parameters = {}

            endpoint_added = True
            try:
                for endpoint in endpoints:
                    self.add_endpoint(endpoint=endpoint,
                                      endpoint_name=endpoint_name,
                                      handler=endpoint_handler,
                                      methods=endpoint_methods)

            except AssertionError:
                endpoint_added = False

            if endpoint_added:
                self.fhdhr.logger.debug("Adding endpoint %s available at %s with %s methods." % (endpoint_name, ",".join(endpoints), ",".join(endpoint_methods)))

                if endpoint_category not in list(self.route_list.keys()):
                    self.route_list[endpoint_category] = {}

                if endpoint_name not in list(self.route_list[endpoint_category].keys()):
                    self.route_list[endpoint_category][endpoint_name] = {}

                self.route_list[endpoint_category][endpoint_name]["name"] = endpoint_name
                self.route_list[endpoint_category][endpoint_name]["endpoints"] = endpoints
                self.route_list[endpoint_category][endpoint_name]["endpoint_methods"] = endpoint_methods
                self.route_list[endpoint_category][endpoint_name]["endpoint_access_level"] = endpoint_access_level
                self.route_list[endpoint_category][endpoint_name]["endpoint_parameters"] = endpoint_parameters
                self.route_list[endpoint_category][endpoint_name]["pretty_name"] = pretty_name
                self.route_list[endpoint_category][endpoint_name]["endpoint_category"] = endpoint_category

    def isapath(self, item):
        """
        Ignore instances.
        """

        if item.startswith("__") and item.endswith("__"):
            return False

        not_a_page_list = ["fhdhr", "plugin_utils", "auto_page_refresh", "pages_to_refresh"]
        if item in not_a_page_list:
            return False

        if item.startswith("proxy_"):
            return False

        return True

    def add_endpoint(self, endpoint=None, endpoint_name=None, handler=None, methods=['GET']):
        """
        Add Endpoint.
        """

        self.fhdhr.app.add_url_rule(endpoint, endpoint_name, handler, methods=methods)

    def run(self):
        """
        Run the WSGIServer.
        """

        self.http = WSGIServer(self.fhdhr.api.address_tuple,
                               self.fhdhr.app.wsgi_app,
                               log=self.fhdhr.logger.logger,
                               error_log=self.fhdhr.logger.logger)
        try:
            self.http.serve_forever()
            self.stop()

        except OSError as exerror:
            error_out = self.fhdhr.logger.lazy_exception(exerror, "HTTP Server Offline")
            self.fhdhr.logger.error(error_out)

        except AttributeError:
            self.fhdhr.logger.info("HTTP Server Offline")
