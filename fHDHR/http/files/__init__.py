

from .favicon_ico import Favicon_ICO
from .style_css import Style_CSS

from .device_xml import Device_XML
from .lineup_xml import Lineup_XML

from .discover_json import Discover_JSON
from .lineup_json import Lineup_JSON
from .lineup_status_json import Lineup_Status_JSON

from .watch import Watch


class fHDHR_Files():

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

        self.favicon = Favicon_ICO(fhdhr)
        self.style = Style_CSS(fhdhr)

        self.device_xml = Device_XML(fhdhr)
        self.lineup_xml = Lineup_XML(fhdhr)

        self.discover_json = Discover_JSON(fhdhr)
        self.lineup_json = Lineup_JSON(fhdhr)
        self.lineup_status_json = Lineup_Status_JSON(fhdhr)

        self.watch = Watch(fhdhr)
