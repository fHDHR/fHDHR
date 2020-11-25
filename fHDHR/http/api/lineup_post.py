from flask import request, abort, Response


class Lineup_Post():
    endpoints = ["/lineup.post"]
    endpoint_name = "api_lineup_post"
    endpoint_methods = ["POST"]

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        if 'scan' in list(request.args.keys()):

            if request.args['scan'] == 'start':
                self.fhdhr.device.station_scan.scan()
                return Response(status=200, mimetype='text/html')

            elif request.args['scan'] == 'abort':
                return Response(status=200, mimetype='text/html')

            else:
                self.fhdhr.logger.warning("Unknown scan command " + request.args['scan'])
                return abort(200, "Not a valid scan command")

        else:
            return abort(501, "Not a valid command")
