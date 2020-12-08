from flask import Response, request
from io import BytesIO
import xml.etree.ElementTree

from fHDHR.tools import sub_el


class RMG_Devices_DeviceKey():
    endpoints = ["/devices/<devicekey>", "/rmg/devices/<devicekey>"]
    endpoint_name = "rmg_devices_devicekey"
    endpoint_methods = ["GET"]

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, devicekey, *args):
        return self.get(devicekey, *args)

    def get(self, devicekey, *args):
        """Returns the identity, capabilities, and current status of the devices and each of its tuners."""

        base_url = request.url_root[:-1]

        out = xml.etree.ElementTree.Element('MediaContainer')
        if devicekey == self.fhdhr.config.dict["main"]["uuid"]:
            out.set('size', "1")
            device_out = sub_el(out, 'Device',
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
                                )

            tuner_status = self.fhdhr.device.tuners.status()

            for tuner_number in list(tuner_status.keys()):
                tuner_dict = tuner_status[tuner_number]

                # Idle
                if tuner_dict["status"] in ["Inactive"]:
                    sub_el(device_out, 'Tuner',
                           index=tuner_number,
                           status="idle",
                           )

                # Streaming
                elif tuner_dict["status"] in ["Active", "Acquired"]:
                    sub_el(device_out, 'Tuner',
                           index=tuner_number,
                           status="streaming",
                           channelIdentifier="id://%s" % tuner_dict["channel"],
                           signalStrength="100",
                           signalQuality="100",
                           symbolQuality="100",
                           lock="1",
                           )

                # Scanning
                elif tuner_dict["status"] in ["Scanning"]:
                    sub_el(device_out, 'Tuner',
                           index=tuner_number,
                           status="scanning",
                           progress="99",
                           channelsFound=str(len(self.fhdhr.device.channels.list)),
                           )

                # TODO networksScanned
                elif tuner_dict["status"] in ["networksScanned"]:
                    sub_el(device_out, 'Tuner',
                           index=tuner_number,
                           status="networksScanned",
                           )

                # Error
                elif tuner_dict["status"] in ["Error"]:
                    sub_el(device_out, 'Tuner',
                           index=tuner_number,
                           status="error",
                           )

        fakefile = BytesIO()
        fakefile.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        fakefile.write(xml.etree.ElementTree.tostring(out, encoding='UTF-8'))
        device_xml = fakefile.getvalue()

        return Response(status=200,
                        response=device_xml,
                        mimetype='application/xml')
