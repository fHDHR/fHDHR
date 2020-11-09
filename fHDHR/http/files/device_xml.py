from flask import Response, request
from io import BytesIO
import xml.etree.ElementTree

from fHDHR.tools import sub_el


class Device_XML():
    endpoints = ["/device.xml"]
    endpoint_name = "device_xml"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        base_url = request.url_root[:-1]

        out = xml.etree.ElementTree.Element('root')
        out.set('xmlns', "urn:schemas-upnp-org:device-1-0")

        sub_el(out, 'URLBase', base_url)

        specVersion_out = sub_el(out, 'specVersion')
        sub_el(specVersion_out, 'major', "1")
        sub_el(specVersion_out, 'minor', "0")

        device_out = sub_el(out, 'device')
        sub_el(device_out, 'deviceType', "urn:schemas-upnp-org:device:MediaServer:1")
        sub_el(device_out, 'friendlyName', self.fhdhr.config.dict["fhdhr"]["friendlyname"])
        sub_el(device_out, 'manufacturer', self.fhdhr.config.dict["fhdhr"]["reporting_manufacturer"])
        sub_el(device_out, 'modelName', self.fhdhr.config.dict["fhdhr"]["reporting_model"])
        sub_el(device_out, 'modelNumber', self.fhdhr.config.dict["fhdhr"]["reporting_model"])
        sub_el(device_out, 'serialNumber')
        sub_el(device_out, 'UDN', "uuid:" + self.fhdhr.config.dict["main"]["uuid"])

        fakefile = BytesIO()
        fakefile.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        fakefile.write(xml.etree.ElementTree.tostring(out, encoding='UTF-8'))
        device_xml = fakefile.getvalue()

        return Response(status=200,
                        response=device_xml,
                        mimetype='application/xml')
