from flask import Response, request
from io import BytesIO
import xml.etree.ElementTree

from fHDHR.tools import sub_el


class Lineup_XML():
    endpoints = ["/lineup.xml"]
    endpoint_name = "lineup_xml"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        base_url = request.url_root[:-1]

        out = xml.etree.ElementTree.Element('Lineup')
        station_list = self.fhdhr.device.channels.get_station_list(base_url)
        for station_item in station_list:
            program_out = sub_el(out, 'Program')
            sub_el(program_out, 'GuideNumber', station_item['GuideNumber'])
            sub_el(program_out, 'GuideName', station_item['GuideName'])
            sub_el(program_out, 'URL', station_item['URL'])

        fakefile = BytesIO()
        fakefile.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        fakefile.write(xml.etree.ElementTree.tostring(out, encoding='UTF-8'))
        lineup_xml = fakefile.getvalue()

        return Response(status=200,
                        response=lineup_xml,
                        mimetype='application/xml')
