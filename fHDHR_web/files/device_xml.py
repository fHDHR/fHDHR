from flask import redirect, session


class Device_XML():
    endpoints = ["/device.xml"]
    endpoint_name = "file_device_xml"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        if self.fhdhr.config.dict["rmg"]["enabled"] and session["is_plexmediaserver"]:
            return redirect("/rmg/device.xml")
        else:
            return redirect("/hdhr/device.xml")
