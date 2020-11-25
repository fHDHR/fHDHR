from flask import Response, request
from io import BytesIO
import xml.etree.ElementTree

from fHDHR.tools import sub_el


class Lineup_XML():
    endpoints = ["/lineup.xml"]
    endpoint_name = "file_lineup_xml"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        base_url = request.url_root[:-1]

        out = xml.etree.ElementTree.Element('Lineup')
        for fhdhr_id in list(self.fhdhr.device.channels.list.keys()):
            channel_obj = self.fhdhr.device.channels.list[fhdhr_id]
            if channel_obj.enabled:
                lineup_dict = channel_obj.lineup_dict()
                lineup_dict["URL"] = base_url + lineup_dict["URL"]
                program_out = sub_el(out, 'Program')
                sub_el(program_out, 'GuideNumber', lineup_dict['GuideNumber'])
                sub_el(program_out, 'GuideName', lineup_dict['GuideName'])
                sub_el(program_out, 'Tags', lineup_dict['Tags'])
                sub_el(program_out, 'URL', lineup_dict['URL'])

        fakefile = BytesIO()
        fakefile.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        fakefile.write(xml.etree.ElementTree.tostring(out, encoding='UTF-8'))
        lineup_xml = fakefile.getvalue()

        return Response(status=200,
                        response=lineup_xml,
                        mimetype='application/xml')
