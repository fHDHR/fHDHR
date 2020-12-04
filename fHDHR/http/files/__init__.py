

from .favicon_ico import Favicon_ICO
from .style_css import Style_CSS
from .device_xml import Device_XML


class fHDHR_Files():

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

        self.favicon = Favicon_ICO(fhdhr)
        self.style = Style_CSS(fhdhr)
        self.device_xml = Device_XML(fhdhr)
