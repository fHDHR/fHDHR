from .devtools_html import DevTools_HTML
from .devtools_api import DevTools_API


class Plugin_OBJ():

    def __init__(self, fhdhr, plugin_utils):
        self.fhdhr = fhdhr
        self.plugin_utils = plugin_utils

        self.devtools_html = DevTools_HTML(fhdhr, plugin_utils)
        self.devtools_api = DevTools_API(fhdhr, plugin_utils)
