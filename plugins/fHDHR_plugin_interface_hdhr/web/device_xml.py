from flask import Response, request
from io import BytesIO
import xml.etree.ElementTree

from fHDHR.tools import sub_el


class HDHR_Device_XML():
    endpoints = ["/hdhr", "/hdhr/", "/hdhr/device.xml"]
    endpoint_name = "hdhr_device_xml"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    @property
    def source(self):
        return self.fhdhr.config.dict["hdhr"]["source"] or self.fhdhr.origins.valid_origins[0]

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):
        """Device.xml referenced from SSDP"""

        base_url = request.url_root[:-1]

        origin = self.source
        origin_plugin_name = self.fhdhr.origins.origins_dict[origin].plugin_utils.plugin_name
        origin_plugin_version = self.fhdhr.origins.origins_dict[origin].plugin_utils.plugin_manifest["version"]

        out = xml.etree.ElementTree.Element('root')
        out.set('xmlns', "urn:schemas-upnp-org:device-1-0")

        sub_el(out, 'URLBase', "%s/hdhr" % base_url)

        specVersion_out = sub_el(out, 'specVersion')
        sub_el(specVersion_out, 'major', "1")
        sub_el(specVersion_out, 'minor', "0")

        device_out = sub_el(out, 'device')

        sub_el(device_out, 'deviceType', "urn:schemas-upnp-org:device:MediaServer:1")

        sub_el(device_out, 'friendlyName', "%s %s" % (self.fhdhr.config.dict["fhdhr"]["friendlyname"], origin))
        sub_el(device_out, 'manufacturer', self.fhdhr.config.dict["hdhr"]["reporting_manufacturer"])
        sub_el(device_out, 'manufacturerURL', "https://github.com/fHDHR/%s" % origin_plugin_name)
        sub_el(device_out, 'modelName', self.fhdhr.config.dict["hdhr"]["reporting_model"])
        sub_el(device_out, 'modelNumber', origin_plugin_version)

        sub_el(device_out, 'serialNumber')

        sub_el(device_out, 'UDN', "uuid:%s%s" % (self.fhdhr.config.dict["main"]["uuid"], origin))

        fakefile = BytesIO()
        fakefile.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        fakefile.write(xml.etree.ElementTree.tostring(out, encoding='UTF-8'))
        device_xml = fakefile.getvalue()

        return Response(status=200,
                        response=device_xml,
                        mimetype='application/xml')
