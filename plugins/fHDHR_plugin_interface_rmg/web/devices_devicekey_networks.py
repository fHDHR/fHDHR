from flask import Response
from io import BytesIO
import xml.etree.ElementTree

from fHDHR.tools import sub_el


class RMG_Devices_DeviceKey_Networks():
    endpoints = ["/rmg/devices/<devicekey>/networks"]
    endpoint_name = "rmg_devices_devicekey_networks"
    endpoint_methods = ["GET"]

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, devicekey, *args):
        return self.get(devicekey, *args)

    def get(self, devicekey, *args):
        """In some cases, channel scanning is a two-step process, where the first stage consists of scanning for networks (this is called "fast scan")."""

        out = xml.etree.ElementTree.Element('MediaContainer')
        if devicekey.startswith(self.fhdhr.config.dict["main"]["uuid"]):
            origin = devicekey.split(self.fhdhr.config.dict["main"]["uuid"])[-1]
            out.set('size', "1")

            sub_el(out, 'Network',
                   key="%s%s" % (self.fhdhr.config.dict["main"]["uuid"], origin),
                   title="%s %s" % (self.fhdhr.config.dict["fhdhr"]["friendlyname"], origin),
                   )

        fakefile = BytesIO()
        fakefile.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        fakefile.write(xml.etree.ElementTree.tostring(out, encoding='UTF-8'))
        device_xml = fakefile.getvalue()

        return Response(status=200,
                        response=device_xml,
                        mimetype='application/xml')
