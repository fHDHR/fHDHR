from flask import Response, request
from io import BytesIO
import xml.etree.ElementTree


class RMG_Devices_DeviceKey_Scan():
    endpoints = ["/rmg/devices/<devicekey>/scan"]
    endpoint_name = "rmg_devices_devicekey_scan"
    endpoint_methods = ["GET", "POST", "DELETE"]

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, devicekey, *args):
        return self.get(devicekey, *args)

    def get(self, devicekey, *args):
        """Starts a background channel scan."""

        if request.method in ["GET", "POST"]:

            network = request.args.get('network', default=None, type=str)
            source = request.args.get('source', default=None, type=int)
            provider = request.args.get('provider', default=1, type=int)

            self.fhdhr.logger.debug("Scan Requested network:%s, source:%s, provider:%s" % (network, source, provider))

            out = xml.etree.ElementTree.Element('MediaContainer')

            if devicekey.startswith(self.fhdhr.config.dict["main"]["uuid"]):
                origin = devicekey.split(self.fhdhr.config.dict["main"]["uuid"])[-1]

                tuner_status = self.fhdhr.device.tuners.status(origin)
                tuner_scanning = 0
                for tuner in list(tuner_status.keys()):
                    if tuner_status[tuner]["status"] == "Scanning":
                        tuner_scanning += 1

                if tuner_scanning:
                    out.set('status', "1")
                    out.set('message', "Scanning")
                else:
                    out.set('status', "0")
                    out.set('message', "Not Scanning")

            fakefile = BytesIO()
            fakefile.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
            fakefile.write(xml.etree.ElementTree.tostring(out, encoding='UTF-8'))
            device_xml = fakefile.getvalue()

            return Response(status=200,
                            response=device_xml,
                            mimetype='application/xml')

        elif request.method in ["DELETE"]:

            out = xml.etree.ElementTree.Element('MediaContainer')
            if devicekey.startswith(self.fhdhr.config.dict["main"]["uuid"]):
                origin = devicekey.split(self.fhdhr.config.dict["main"]["uuid"])[-1]

                self.fhdhr.device.tuners.stop_tuner_scan(origin)
                out.set('status', "0")
                out.set('message', "Scan Aborted")

            fakefile = BytesIO()
            fakefile.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
            fakefile.write(xml.etree.ElementTree.tostring(out, encoding='UTF-8'))
            device_xml = fakefile.getvalue()
