from flask import Response, request
from io import BytesIO
import xml.etree.ElementTree

from fHDHR.tools import sub_el


class RMG_Devices_Discover():
    endpoints = ["/devices/discover", "/rmg/devices/discover"]
    endpoint_name = "rmg_devices_discover"
    endpoint_methods = ["GET", "POST"]

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):
        """This endpoint requests the grabber attempt to discover any devices it can, and it returns zero or more devices."""

        base_url = request.url_root[:-1]

        out = xml.etree.ElementTree.Element('MediaContainer')
        out.set('size', "1")
        sub_el(out, 'Device',
               key=self.fhdhr.config.dict["main"]["uuid"],
               make=self.fhdhr.config.dict["fhdhr"]["reporting_manufacturer"],
               model=self.fhdhr.config.dict["fhdhr"]["reporting_model"],
               modelNumber=self.fhdhr.config.internal["versions"]["fHDHR"],
               protocol="livetv",
               status="alive",
               title=self.fhdhr.config.dict["fhdhr"]["friendlyname"],
               tuners=str(self.fhdhr.config.dict["fhdhr"]["tuner_count"]),
               uri=base_url,
               uuid="device://tv.plex.grabbers.fHDHR/%s" % self.fhdhr.config.dict["main"]["uuid"],
               thumb="favicon.ico",
               interface='network'
               # TODO add preferences
               )

        fakefile = BytesIO()
        fakefile.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        fakefile.write(xml.etree.ElementTree.tostring(out, encoding='UTF-8'))
        device_xml = fakefile.getvalue()

        return Response(status=200,
                        response=device_xml,
                        mimetype='application/xml')
