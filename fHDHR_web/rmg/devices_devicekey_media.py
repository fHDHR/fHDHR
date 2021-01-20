from flask import request, redirect
import urllib.parse


class RMG_Devices_DeviceKey_Media():
    endpoints = ["/devices/<devicekey>/media/<channel>", "/rmg/devices/<devicekey>/media/<channel>"]
    endpoint_name = "rmg_devices_devicekey_media"
    endpoint_methods = ["GET"]

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, devicekey, channel, *args):
        return self.get(devicekey, channel, *args)

    def get(self, devicekey, channel, *args):

        param = request.args.get('method', default=None, type=str)
        self.fhdhr.logger.debug("param:%s" % param)

        method = self.fhdhr.config.dict["streaming"]["method"]

        redirect_url = "/api/tuners?method=%s" % (method)

        if str(channel).startswith('id://'):
            channel = str(channel).replace('id://', '')
        redirect_url += "&channel=%s" % str(channel)

        redirect_url += "&accessed=%s" % urllib.parse.quote(request.url)

        return redirect(redirect_url)
