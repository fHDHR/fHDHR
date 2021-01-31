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

        client_address = request.remote_addr

        accessed_url = request.args.get('accessed', default=request.url, type=str)

        method = request.args.get('method', default=self.fhdhr.config.dict["streaming"]["method"], type=str)

        tuner_number = request.args.get('tuner', default=None, type=str)

        redirect_url = request.args.get('redirect', default=None, type=str)

        origin_methods = self.fhdhr.origins.valid_origins
        origin = request.args.get('origin', default=None, type=str)
        if origin and origin not in origin_methods:
            return "%s Invalid channels origin" % origin

        if method == "stream":

            channel_number = request.args.get('channel', None, type=str)
            if not channel_number:
                return "Missing Channel"

            if origin:

                if str(channel_number) in [str(x) for x in self.fhdhr.device.channels.get_channel_list("number", origin)]:
                    chan_obj = self.fhdhr.device.channels.get_channel_obj("number", channel_number, origin)
                elif str(channel_number) in [str(x) for x in self.fhdhr.device.channels.get_channel_list("id", origin)]:
                    chan_obj = self.fhdhr.device.channels.get_channel_obj("id", channel_number, origin)
                else:
                    response = Response("Not Found", status=404)
                    response.headers["X-fHDHR-Error"] = "801 - Unknown Channel"
                    self.fhdhr.logger.error(response.headers["X-fHDHR-Error"])
                    abort(response)

            else:

                if str(channel_number) in [str(x) for x in self.fhdhr.device.channels.get_channel_list("id")]:
                    chan_obj = self.fhdhr.device.channels.get_channel_obj("id", channel_number)
                else:
                    response = Response("Not Found", status=404)
                    response.headers["X-fHDHR-Error"] = "801 - Unknown Channel"
                    self.fhdhr.logger.error(response.headers["X-fHDHR-Error"])
                    abort(response)

            if not chan_obj.dict["enabled"]:
                response = Response("Service Unavailable", status=503)
                response.headers["X-fHDHR-Error"] = str("806 - Tune Failed")
                self.fhdhr.logger.error(response.headers["X-fHDHR-Error"])
                abort(response)

            origin = chan_obj.origin
            channel_number = chan_obj.number

            stream_method = request.args.get('stream_method', default=self.fhdhr.origins.origins_dict[origin].stream_method, type=str)
            if stream_method not in list(self.fhdhr.config.dict["streaming"]["valid_methods"].keys()):
                response = Response("Service Unavailable", status=503)
                response = Response("Service Unavailable", status=503)
                response.headers["X-fHDHR-Error"] = str("806 - Tune Failed")
                abort(response)

            duration = request.args.get('duration', default=0, type=int)

            transcode_quality = request.args.get('transcode', default=None, type=str)
            valid_transcode_types = [None, "heavy", "mobile", "internet720", "internet480", "internet360", "internet240"]
            if transcode_quality not in valid_transcode_types:
                response = Response("Service Unavailable", status=503)
                response.headers["X-fHDHR-Error"] = "802 - Unknown Transcode Profile"
                self.fhdhr.logger.error(response.headers["X-fHDHR-Error"])
                abort(response)

            stream_args = {
                            "channel": channel_number,
                            "origin": origin,
                            "method": stream_method,
                            "duration": duration,
                            "origin_quality": self.fhdhr.config.dict["streaming"]["origin_quality"],
                            "transcode_quality": transcode_quality or self.fhdhr.config.dict["streaming"]["transcode_quality"],
                            "accessed": accessed_url,
                            "client": client_address,
                            "client_id": session["session_id"]
                            }

            try:
                if not tuner_number:
                    tunernum = self.fhdhr.device.tuners.first_available(origin, channel_number)
                else:
                    tunernum = self.fhdhr.device.tuners.tuner_grab(tuner_number, origin, channel_number)
            except TunerError as e:
                self.fhdhr.logger.info("A %s stream request for channel %s was rejected due to %s"
                                       % (stream_args["method"], str(stream_args["channel"]), str(e)))
                response = Response("Service Unavailable", status=503)
                response.headers["X-fHDHR-Error"] = str(e)
                self.fhdhr.logger.error(response.headers["X-fHDHR-Error"])
                abort(response)

            tuner = self.fhdhr.device.tuners.tuners[origin][str(tunernum)]

            try:
                stream_args = self.fhdhr.device.tuners.get_stream_info(stream_args)
            except TunerError as e:
                self.fhdhr.logger.info("A %s stream request for %s channel %s was rejected due to %s"
                                       % (origin, stream_args["method"], str(stream_args["channel"]), str(e)))
                response = Response("Service Unavailable", status=503)
                response.headers["X-fHDHR-Error"] = str(e)
                self.fhdhr.logger.error(response.headers["X-fHDHR-Error"])
                tuner.close()
                abort(response)

            self.fhdhr.logger.info("%s Tuner #%s to be used for stream." % (origin, tunernum))
            tuner.set_status(stream_args)
            session["tuner_used"] = tunernum

            try:
                stream = tuner.get_stream(stream_args, tuner)
            except TunerError as e:
                response.headers["X-fHDHR-Error"] = str(e)
                self.fhdhr.logger.error(response.headers["X-fHDHR-Error"])
                tuner.close()
                abort(response)

            return Response(stream_with_context(stream.get()), mimetype=stream_args["content_type"])

        elif method == "close":

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
            return redirect("%s?retmessage=%s" % (redirect_url, urllib.parse.quote("%s Success" % method)))
        else:
            return "%s Success" % method
