from gevent.pywsgi import WSGIServer
from flask import Flask

from .pages import fHDHR_Pages
from .files import fHDHR_Files
from .api import fHDHR_API
from .watch import fHDHR_WATCH


class fHDHR_HTTP_Server():
    app = None

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

        self.template_folder = fhdhr.config.dict["filedir"]["www_templates_dir"]

        self.app = Flask("fHDHR", template_folder=self.template_folder)

        self.pages = fHDHR_Pages(fhdhr)
        self.add_endpoints(self.pages, "pages")

        self.files = fHDHR_Files(fhdhr)
        self.add_endpoints(self.files, "files")

        self.api = fHDHR_API(fhdhr)
        self.add_endpoints(self.api, "api")

        self.watch = fHDHR_WATCH(fhdhr)
        self.add_endpoints(self.watch, "watch")

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
            for endpoint in endpoints:
                self.add_endpoint(endpoint=endpoint,
                                  endpoint_name=endpoint_name,
                                  handler=handler,
                                  methods=endpoint_methods)

    def isapath(self, item):
        not_a_page_list = ["fhdhr", "htmlerror", "page_elements"]
        if item in not_a_page_list:
            return False
        elif item.startswith("__") and item.endswith("__"):
            return False
        else:
            return True

    def add_endpoint(self, endpoint=None, endpoint_name=None, handler=None, methods=['GET']):
        self.app.add_url_rule(endpoint, endpoint_name, handler, methods=methods)

    def run(self):
        self.http = WSGIServer((
                            self.fhdhr.config.dict["fhdhr"]["address"],
                            int(self.fhdhr.config.dict["fhdhr"]["port"])
                            ), self.app.wsgi_app)
        try:
            self.http.serve_forever()
        except KeyboardInterrupt:
            self.http.stop()
