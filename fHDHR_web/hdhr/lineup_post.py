from flask import request, abort, Response

from fHDHR.exceptions import TunerError


class Lineup_Post():
    endpoints = ["/lineup.post", "/hdhr/lineup.post"]
    endpoint_name = "hdhr_lineup_post"
    endpoint_methods = ["POST"]

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        if 'scan' in list(request.args.keys()):

            if request.args['scan'] == 'start':
                try:
                    self.fhdhr.device.tuners.tuner_scan()
                except TunerError as e:
                    self.fhdhr.logger.info(str(e))
                return Response(status=200, mimetype='text/html')

            elif request.args['scan'] == 'abort':
                self.fhdhr.device.tuners.stop_tuner_scan()
                return Response(status=200, mimetype='text/html')

            else:
                self.fhdhr.logger.warning("Unknown scan command %s" % request.args['scan'])
                return abort(200, "Not a valid scan command")

        elif 'favorite' in list(request.args.keys()):
            if request.args['favorite'].startstwith(tuple(["+", "-", "x"])):

                channel_method = request.args['favorite'][0]
                channel_number = request.args['favorite'][1:]

                if str(channel_number) not in [str(x) for x in self.fhdhr.device.channels.get_channel_list("number")]:
                    response = Response("Not Found", status=404)
                    response.headers["X-fHDHR-Error"] = "801 - Unknown Channel"
                    self.fhdhr.logger.error(response.headers["X-fHDHR-Error"])
                    abort(response)

                if channel_method == "+":
                    self.fhdhr.device.channels.set_channel_enablement("number", channel_number, channel_method)
                elif channel_method == "-":
                    self.fhdhr.device.channels.set_channel_enablement("number", channel_number, channel_method)
                elif channel_method == "x":
                    self.fhdhr.device.channels.set_channel_enablement("number", channel_number, "toggle")

            else:
                self.fhdhr.logger.warning("Unknown favorite command %s" % request.args['favorite'])
                return abort(200, "Not a valid favorite command")

        else:
            return abort(501, "Not a valid command")
