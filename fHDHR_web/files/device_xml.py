from flask import request, redirect


class Device_XML():
    endpoints = ["/device.xml"]
    endpoint_name = "file_device_xml"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        user_agent = request.headers.get('User-Agent')
        if (self.fhdhr.config.dict["rmg"]["enabled"] and
           str(user_agent).lower().startswith("plexmediaserver")):
            return redirect("/rmg/device.xml")
        else:
            return redirect("/hdhr/device.xml")
