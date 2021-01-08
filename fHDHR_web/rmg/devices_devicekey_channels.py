from flask import Response
from io import BytesIO
import xml.etree.ElementTree

from fHDHR.tools import sub_el


class RMG_Devices_DeviceKey_Channels():
    endpoints = ["/devices/<devicekey>/channels", "/rmg/devices/<devicekey>/channels"]
    endpoint_name = "rmg_devices_devicekey_channels"
    endpoint_methods = ["GET"]

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, devicekey, *args):
        return self.get(devicekey, *args)

    def get(self, devicekey, *args):
        """Returns the current channels."""

        out = xml.etree.ElementTree.Element('MediaContainer')
        if devicekey == self.fhdhr.config.dict["main"]["uuid"]:
            out.set('size', str(len(self.fhdhr.device.channels.list)))
            for fhdhr_id in [x["id"] for x in self.fhdhr.device.channels.get_channels()]:
                channel_obj = self.fhdhr.device.channels.list[fhdhr_id]
                if channel_obj.enabled:
                    sub_el(out, 'Channel',
                           drm="0",
                           channelIdentifier=channel_obj.rmg_stream_ident,
                           name=channel_obj.dict["name"],
                           origin=channel_obj.dict["callsign"],
                           number=str(channel_obj.number),
                           type="tv",
                           # TODO param
                           signalStrength="100",
                           signalQuality="100",
                           )

        fakefile = BytesIO()
        fakefile.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        fakefile.write(xml.etree.ElementTree.tostring(out, encoding='UTF-8'))
        device_xml = fakefile.getvalue()

        return Response(status=200,
                        response=device_xml,
                        mimetype='application/xml')
