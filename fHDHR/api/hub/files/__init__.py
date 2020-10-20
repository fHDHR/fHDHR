# pylama:ignore=W0611
from .discover_json import Discover_JSON
from .device_xml import Device_XML
from .lineup_xml import Lineup_XML
from .lineup_json import Lineup_JSON
from .debug_json import Debug_JSON
from .lineup_status_json import Lineup_Status_JSON
from .xmltv_xml import xmlTV_XML
from .channels_m3u import channels_M3U


class fHDHR_Files():

    def __init__(self, settings, device):
        self.config = settings
        self.device = device

        self.discoverjson = Discover_JSON(settings)
        self.devicexml = Device_XML(settings)

        self.lineupxml = Lineup_XML(settings, device)
        self.lineupjson = Lineup_JSON(settings, device)
        self.lineupstatusjson = Lineup_Status_JSON(settings, device)

        self.xmltv = xmlTV_XML(settings, device)
        self.m3u = channels_M3U(settings, device)

        self.debug = Debug_JSON(settings, device)
