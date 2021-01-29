from flask import Response


class RMG_Devices_DeviceKey_Prefs():
    endpoints = ["/rmg/devices/<devicekey>/prefs"]
    endpoint_name = "rmg_devices_devicekey_prefs"
    endpoint_methods = ["GET", "PUT"]

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, devicekey, *args):
        return self.get(devicekey, *args)

    def get(self, devicekey, *args):
        """Prefs sent back from Plex in Key-Pair format"""

        if devicekey.startswith(self.fhdhr.config.dict["main"]["uuid"]):
            return Response(status=200)

        return Response(status=200)
