from flask import Response, request
from io import BytesIO
import xml.etree.ElementTree

from fHDHR.tools import sub_el


class Cluster_Device_XML():
    endpoints = ["/cluster/device.xml"]
    endpoint_name = "cluster_device_xml"

    def __init__(self, fhdhr, plugin_utils):
        self.fhdhr = fhdhr
        self.plugin_utils = plugin_utils

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):
        """Device.xml referenced from SSDP"""

        base_url = request.url_root[:-1]

        out = xml.etree.ElementTree.Element('root')
        out.set('xmlns', "upnp:rootdevice")

        sub_el(out, 'URLBase', "%s" % base_url)

        specVersion_out = sub_el(out, 'specVersion')
        sub_el(specVersion_out, 'major', "1")
        sub_el(specVersion_out, 'minor', "0")

        device_out = sub_el(out, 'device')

        sub_el(device_out, 'deviceType', "upnp:rootdevice")
        sub_el(device_out, 'friendlyName', self.fhdhr.config.dict["fhdhr"]["friendlyname"])
        sub_el(device_out, 'UDN', "uuid:%s" % self.fhdhr.config.dict["main"]["uuid"])

        fakefile = BytesIO()
        fakefile.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        fakefile.write(xml.etree.ElementTree.tostring(out, encoding='UTF-8'))
        device_xml = fakefile.getvalue()

        return Response(status=200,
                        response=device_xml,
                        mimetype='application/xml')
