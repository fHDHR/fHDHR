from flask import Response, request
from io import BytesIO
import xml.etree.ElementTree

from fHDHR.tools import sub_el


class RMG_Devices_DeviceKey_Scanners():
    endpoints = ["/rmg/devices/<devicekey>/scanners"]
    endpoint_name = "rmg_devices_devicekey_scanners"
    endpoint_methods = ["GET"]

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, devicekey, *args):
        return self.get(devicekey, *args)

    def get(self, devicekey, *args):
        """ascertain which type of scanners are supported."""

        method = request.args.get('type', default="0", type=str)
        # 0 (atsc), 1 (cqam), 2 (dvb-s), 3 (iptv), 4 (virtual), 5 (dvb-t), 6 (dvb-c), 7 (isdbt)

        out = xml.etree.ElementTree.Element('MediaContainer')
        if devicekey.startswith(self.fhdhr.config.dict["main"]["uuid"]):
            origin = devicekey.split(self.fhdhr.config.dict["main"]["uuid"])[-1]

            if method == "0":
                out.set('size', "1")
                out.set('simultaneousScanners', "1")

                scanner_out = sub_el(out, 'Scanner',
                                     type="atsc",
                                     # TODO country
                                     )
                sub_el(scanner_out, 'Setting',
                       id="provider",
                       type="text",
                       enumValues=origin
                       )

        fakefile = BytesIO()
        fakefile.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        fakefile.write(xml.etree.ElementTree.tostring(out, encoding='UTF-8'))
        device_xml = fakefile.getvalue()

        return Response(status=200,
                        response=device_xml,
                        mimetype='application/xml')
