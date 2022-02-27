from flask import Response, request, redirect, abort, stream_with_context, session
import urllib.parse
import json

from fHDHR.exceptions import TunerError


class Tuners():
    endpoints = ["/api/tuners"]
    endpoint_name = "api_tuners"
    endpoint_methods = ["GET", "POST"]
    endpoint_default_parameters = {
                                    "method": "status"
                                    }

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        method = request.args.get('method', default="stream", type=str)

        if method == "stream":

            streammanager = self.fhdhr.streammanager

            tune_error = None
            try:
                stream_obj, stream_args, response_dict = streammanager.setup_stream(request, session)
            except TunerError as tune_error:
                stream_obj, stream_args = None, None
                response_dict = {"message": "Service Unavailable", "status_code": 503, "headers": tune_error}

            if not stream_obj or tune_error:
                self.fhdhr.logger.error("Unable to Stream: %s" % response_dict["headers"])
                response = Response(response_dict["message"], status=response_dict["status_code"])
                response.headers["X-fHDHR-Error"] = response_dict["headers"]
                if stream_obj:
                    if stream_obj.tuner:
                        stream_obj.tuner.close()
                abort(response)

            if stream_args["method"] == "passthrough":
                self.fhdhr.logger.info("Passthrough method selected, no tuner will be used. Redirecting Client to %s" % stream_args["stream_info"]["url"])
                return redirect(stream_args["stream_info"]["url"])

            return Response(stream_with_context(stream_obj.stream.get()), mimetype=stream_args["content_type"])

        """All other Tuner API Methods"""

        origin = request.args.get('origin', default=None, type=str)
        if origin and origin not in self.fhdhr.origins.valid_origins:
            response = Response("Not Found", status=404)
            response.headers["X-fHDHR-Error"] = "801 - Unknown Origin"
            self.fhdhr.logger.error(response.headers["X-fHDHR-Error"])
            abort(response)

        redirect_url = request.args.get('redirect', default=None, type=str)

        tuner_number = request.args.get('tuner', default=None, type=str)

        if method == "close":

            if not origin:
                return "Missing Origin"

            if not tuner_number or str(tuner_number) not in list(self.fhdhr.device.tuners.tuners[origin].keys()):
                return "%s Invalid tuner" % str(tuner_number)

            session["tuner_used"] = tuner_number

            tuner = self.fhdhr.device.tuners.tuners[origin][str(tuner_number)]
            tuner.close()

        elif method == "scan":

            if not origin:
                for origin in list(self.fhdhr.device.tuners.tuners.keys()):
                    if not tuner_number:
                        tunernum = self.fhdhr.device.tuners.first_available(origin, None)
                    else:
                        tunernum = self.fhdhr.device.tuners.tuner_grab(tuner_number, origin, None)
                    tuner = self.fhdhr.device.tuners.tuners[origin][str(tunernum)]
                    tuner.channel_scan(origin=origin, grabbed=False)
            else:
                if not tuner_number:
                    tunernum = self.fhdhr.device.tuners.first_available(origin, None)
                else:
                    tunernum = self.fhdhr.device.tuners.tuner_grab(tuner_number, origin, None)
                tuner = self.fhdhr.device.tuners.tuners[origin][str(tunernum)]
                tuner.channel_scan(origin=origin, grabbed=True)

        elif method == "status":

            if not origin:
                if not tuner_number:
                    tuner_status = self.fhdhr.device.tuners.status()
                else:
                    tuner_status = ["Invalid Tuner %s" % tuner_number]
            else:

                if not tuner_number:
                    tuner_status = self.fhdhr.device.tuners.status(origin)
                elif str(tuner_number) in list(self.fhdhr.device.tuners.tuners[origin].keys()):
                    tuner_status = self.fhdhr.device.tuners.tuners[origin][str(tuner_number)].get_status()
                else:
                    tuner_status = ["Invalid Tuner %s" % tuner_number]

            tuner_status_json = json.dumps(tuner_status, indent=4)

            return Response(status=200,
                            response=tuner_status_json,
                            mimetype='application/json')

        else:
            return "%s Invalid Method" % method

        if redirect_url:
            if "?" in redirect_url:
                return redirect("%s&retmessage=%s" % (redirect_url, urllib.parse.quote("%s Success" % method)))
            else:
                return redirect("%s?retmessage=%s" % (redirect_url, urllib.parse.quote("%s Success" % method)))
        else:
            return "%s Success" % method
