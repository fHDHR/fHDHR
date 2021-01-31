from flask import request, redirect, abort, Response
import urllib.parse


class RMG_Devices_DeviceKey_Media():
    endpoints = ["/rmg/devices/<devicekey>/media/<channel>"]
    endpoint_name = "rmg_devices_devicekey_media"
    endpoint_methods = ["GET"]

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, devicekey, channel, *args):
        return self.get(devicekey, channel, *args)

    def get(self, devicekey, channel, *args):

        param = request.args.get('method', default=None, type=str)
        self.fhdhr.logger.debug("param:%s" % param)

        if not devicekey.startswith(self.fhdhr.config.dict["main"]["uuid"]):
            response = Response("Not Found", status=404)
            response.headers["X-fHDHR-Error"] = "801 - Unknown devicekey"
            self.fhdhr.logger.error(response.headers["X-fHDHR-Error"])
            abort(response)
        origin = devicekey.split(self.fhdhr.config.dict["main"]["uuid"])[-1]

        redirect_url = "/api/tuners?method=stream"

        if str(channel).startswith('id://'):
            channel = str(channel).replace('id://', '')
        elif channel.startswith("triplet://"):
            channel_tuple = channel.replace('triplet://', '').split(":")
            self.fhdhr.logger.error("Not Implemented %s" % ":".join(channel_tuple))
            abort(501, "Not Implemented %s" % ":".join(channel_tuple))

        redirect_url += "&channel=%s" % (channel)
        redirect_url += "&origin=%s" % (origin)
        redirect_url += "&stream_method=%s" % self.fhdhr.origins.origins_dict[origin].stream_method

        redirect_url += "&accessed=%s" % urllib.parse.quote(request.url)

        return redirect(redirect_url)
