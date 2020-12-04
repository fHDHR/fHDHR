from flask import Response


class RMG_Devices_DeviceKey_Prefs():
    endpoints = ["/devices/<devicekey>/prefs", "/rmg/devices/<devicekey>/prefs"]
    endpoint_name = "rmg_devices_devicekey_prefs"
    endpoint_methods = ["GET", "PUT"]

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, devicekey, *args):
        return self.get(devicekey, *args)

    def get(self, devicekey, *args):
        """Prefs sent back from Plex in Key-Pair format"""

        return Response(status=200)
