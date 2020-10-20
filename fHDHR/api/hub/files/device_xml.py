import xml.etree.ElementTree
from io import BytesIO

from fHDHR.tools import sub_el


class Device_XML():
    device_xml = None

    def __init__(self, settings):
        self.config = settings

    def get_device_xml(self, base_url, force_update=False):
        if not self.device_xml or force_update:
            out = xml.etree.ElementTree.Element('root')
            out.set('xmlns', "urn:schemas-upnp-org:device-1-0")

            sub_el(out, 'URLBase', "http://" + base_url)

            specVersion_out = sub_el(out, 'specVersion')
            sub_el(specVersion_out, 'major', "1")
            sub_el(specVersion_out, 'minor', "0")

            device_out = sub_el(out, 'device')
            sub_el(device_out, 'deviceType', "urn:schemas-upnp-org:device:MediaServer:1")
            sub_el(device_out, 'friendlyName', self.config.dict["fhdhr"]["friendlyname"])
            sub_el(device_out, 'manufacturer', self.config.dict["dev"]["reporting_manufacturer"])
            sub_el(device_out, 'modelName', self.config.dict["dev"]["reporting_model"])
            sub_el(device_out, 'modelNumber', self.config.dict["dev"]["reporting_model"])
            sub_el(device_out, 'serialNumber')
            sub_el(device_out, 'UDN', "uuid:" + self.config.dict["main"]["uuid"])

            fakefile = BytesIO()
            fakefile.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
            fakefile.write(xml.etree.ElementTree.tostring(out, encoding='UTF-8'))
            self.device_xml = fakefile.getvalue()

        return self.device_xml
