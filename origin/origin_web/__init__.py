
from .origin_api import Origin_API
from .origin_api_tools import Origin_API_Tools
from .origin_html import Origin_HTML


class fHDHR_Origin_Web():

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

        self.origin_api = Origin_API(fhdhr)
        self.origin_api_tools = Origin_API_Tools(fhdhr)
        self.origin_html = Origin_HTML(fhdhr)
