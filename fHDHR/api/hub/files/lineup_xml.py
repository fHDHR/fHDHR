import xml.etree.ElementTree
from io import BytesIO

from fHDHR.tools import sub_el


class Lineup_XML():
    device_xml = None

    def __init__(self, settings, device):
        self.config = settings
        self.device = device

    def get_lineup_xml(self, base_url, force_update=False):
        if not self.device_xml or force_update:
            out = xml.etree.ElementTree.Element('Lineup')
            station_list = self.device.channels.get_station_list(base_url)
            for station_item in station_list:
                program_out = sub_el(out, 'Program')
                sub_el(program_out, 'GuideNumber', station_item['GuideNumber'])
                sub_el(program_out, 'GuideName', station_item['GuideName'])
                sub_el(program_out, 'URL', station_item['URL'])

            fakefile = BytesIO()
            fakefile.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
            fakefile.write(xml.etree.ElementTree.tostring(out, encoding='UTF-8'))
            self.device_xml = fakefile.getvalue()

        return self.device_xml
