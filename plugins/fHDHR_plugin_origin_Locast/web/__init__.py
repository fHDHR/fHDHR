
from .locast_api import Locast_API
from .locast_api_tools import Locast_API_Tools
from .locast_html import Locast_HTML


class Plugin_OBJ():

    def __init__(self, fhdhr, plugin_utils):
        self.fhdhr = fhdhr
        self.plugin_utils = plugin_utils

        self.locast_api = Locast_API(plugin_utils)
        self.locast_api_tools = Locast_API_Tools(plugin_utils)
        self.locast_html = Locast_HTML(fhdhr, plugin_utils)
