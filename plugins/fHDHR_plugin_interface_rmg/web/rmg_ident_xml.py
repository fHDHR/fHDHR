from flask import Response, request
from io import BytesIO
import xml.etree.ElementTree

from fHDHR.tools import sub_el


class RMG_Ident_XML():
    endpoints = ["/rmg/<devicekey>/"]
    endpoint_name = "rmg_ident_xml"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, devicekey, *args):
        """Device.xml referenced from SSDP"""
        """Provides general information about the media grabber"""

        base_url = request.url_root[:-1]

        out = xml.etree.ElementTree.Element('MediaContainer')
        if devicekey.startswith(self.fhdhr.config.dict["main"]["uuid"]):
            origin = devicekey.split(self.fhdhr.config.dict["main"]["uuid"])[-1]

            sub_el(out, 'MediaGrabber',
                   identifier="tv.plex.grabbers.fHDHR.%s" % origin,
                   title="%s %s" % (self.fhdhr.config.dict["fhdhr"]["friendlyname"], origin),
                   protocols="livetv",
                   icon="%s/favicon.ico" % base_url
                   )

        fakefile = BytesIO()
        fakefile.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        fakefile.write(xml.etree.ElementTree.tostring(out, encoding='UTF-8'))
        device_xml = fakefile.getvalue()

        return Response(status=200,
                        response=device_xml,
                        mimetype='application/xml')
