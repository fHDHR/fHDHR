from flask import Response, request
from io import BytesIO
import xml.etree.ElementTree

from fHDHR.tools import sub_el


class RMG_Devices_DeviceKey():
    endpoints = ["/rmg/devices/<devicekey>"]
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

        if devicekey.startswith(self.fhdhr.config.dict["main"]["uuid"]):
            origin = devicekey.split(self.fhdhr.config.dict["main"]["uuid"])[-1]
            out.set('size', "1")

            if self.fhdhr.origins.origins_dict[origin].setup_success:
                alive_status = "alive"
            else:
                alive_status = "dead"

            device_out = sub_el(out, 'Device',
                                key="%s%s" % (self.fhdhr.config.dict["main"]["uuid"], origin),
                                make=self.fhdhr.config.dict["rmg"]["reporting_manufacturer"],
                                model=self.fhdhr.config.dict["rmg"]["reporting_model"],
                                modelNumber=self.fhdhr.config.internal["versions"]["fHDHR"],
                                protocol="livetv",
                                status=alive_status,
                                title="%s %s" % (self.fhdhr.config.dict["fhdhr"]["friendlyname"], origin),
                                tuners=str(self.fhdhr.origins.origins_dict[origin].tuners),
                                uri="%s/rmg/%s%s" % (base_url, self.fhdhr.config.dict["main"]["uuid"], origin),
                                uuid="device://tv.plex.grabbers.fHDHR/%s%s" % (self.fhdhr.config.dict["main"]["uuid"], origin),
                                )

            tuner_status = self.fhdhr.device.tuners.status(origin)

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
                           channelsFound=str(len(list(self.fhdhr.device.channels.list[origin].keys()))),
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
