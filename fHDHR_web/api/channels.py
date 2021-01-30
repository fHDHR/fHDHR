from flask import request, redirect, Response, abort
import urllib.parse
import json

from fHDHR.tools import channel_sort


class Channels():
    endpoints = ["/api/channels"]
    endpoint_name = "api_channels"
    endpoint_methods = ["GET", "POST"]
    endpoint_default_parameters = {
                                    "method": "get"
                                    }

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        method = request.args.get('method', default=None, type=str)
        redirect_url = request.args.get('redirect', default=None, type=str)

        origin_methods = self.fhdhr.origins.valid_origins
        origin = request.args.get('origin', default=None, type=str)
        if origin and origin not in origin_methods:
            return "%s Invalid channels origin" % origin

        if method == "get":
            channels_info = {}
            if not origin:
                origin_list = origin_methods
            else:
                origin_list = [origin]

            for origin_item in origin_list:

                channels_info[origin_item] = {}

                for fhdhr_id in [x["id"] for x in self.fhdhr.device.channels.get_channels(origin=origin_item)]:
                    channel_obj = self.fhdhr.device.channels.list[origin_item][fhdhr_id]
                    channel_dict = channel_obj.dict.copy()
                    channel_dict["m3u_url"] = channel_obj.api_m3u_url
                    channel_dict["stream_url"] = channel_obj.api_stream_url
                    channels_info[origin_item][channel_obj.number] = channel_dict

                # Sort the channels
                sorted_channel_list = channel_sort(list(channels_info[origin_item].keys()))
                sorted_chan_guide = []
                for channel in sorted_channel_list:
                    sorted_chan_guide.append(channels_info[origin_item][channel])

                channels_info[origin_item] = sorted_chan_guide

            channels_info_json = json.dumps(channels_info, indent=4)

            return Response(status=200,
                            response=channels_info_json,
                            mimetype='application/json')

        elif method == "favorite":

            channel = request.args.get('channel', default=None, type=str)
            if not channel:
                if redirect_url:
                    return redirect("%s?retmessage=%s" % (redirect_url, urllib.parse.quote("%s Failed" % method)))
                else:
                    return "%s Falied" % method

            if channel.startstwith(tuple(["+", "-", "x"])):

                channel_method = channel[0]
                channel_number = channel[1:]

                if str(channel_number) not in [str(x) for x in self.fhdhr.device.channels.get_channel_list("number", origin)]:
                    response = Response("Not Found", status=404)
                    response.headers["X-fHDHR-Error"] = "801 - Unknown Channel"
                    self.fhdhr.logger.error(response.headers["X-fHDHR-Error"])
                    abort(response)

                if channel_method == "+":
                    self.fhdhr.device.channels.set_channel_enablement("number", channel_number, channel_method, origin)
                elif channel_method == "-":
                    self.fhdhr.device.channels.set_channel_enablement("number", channel_number, channel_method, origin)
                elif channel_method == "x":
                    self.fhdhr.device.channels.set_channel_enablement("number", channel_number, "toggle", origin)

            else:
                self.fhdhr.logger.warning("Unknown favorite command %s" % request.args['favorite'])
                return abort(200, "Not a valid favorite command")

        elif method in ["enable", "disable"]:
            channel = request.args.get('channel', default=None, type=str)
            if channel == "all":
                self.fhdhr.device.channels.set_channel_enablement_all(method, origin)
            elif not channel or str(channel) not in [str(x) for x in self.fhdhr.device.channels.get_channel_list("number", origin)]:
                if redirect_url:
                    return redirect("%s?retmessage=%s" % (redirect_url, urllib.parse.quote("%s Failed" % method)))
                else:
                    return "%s Falied" % method
            else:
                self.fhdhr.device.channels.set_channel_enablement("number", channel, method, origin)

        elif method == "update":
            channel_id = request.form.get('id', None)
            updatedict = {}
            for key in list(request.form.keys()):
                if key != "id":
                    if key in ["name", "callsign", "thumbnail"]:
                        updatedict[key] = str(request.form.get(key))
                    elif key in ["number"]:
                        number = str(request.form.get(key))
                        if "." in number:
                            updatedict["subnumber"] = number.split(".")[1]
                            updatedict["number"] = number.split(".")[0]
                        else:
                            updatedict["number"] = number
                    elif key in ["enabled"]:
                        confvalue = request.form.get(key)
                        if str(confvalue).lower() in ["false"]:
                            confvalue = False
                        elif str(confvalue).lower() in ["true"]:
                            confvalue = True
                        updatedict[key] = confvalue
                    elif key in ["favorite", "HD"]:
                        updatedict[key] = int(request.form.get(key))
            self.fhdhr.device.channels.set_channel_status("id", channel_id, updatedict, origin)

        elif method == "modify":
            channels_list = json.loads(request.form.get('channels', []))
            for channel in channels_list:
                updatedict = {}
                for key in list(channel.keys()):
                    if key != "id":
                        if key in ["name", "callsign", "thumbnail"]:
                            updatedict[key] = str(channel[key])
                        elif key in ["number"]:
                            number = str(channel[key])
                            if "." in number:
                                updatedict["subnumber"] = number.split(".")[1]
                                updatedict["number"] = number.split(".")[0]
                            else:
                                updatedict["number"] = number
                        elif key in ["enabled"]:
                            confvalue = channel[key]
                            if str(confvalue).lower() in ["false"]:
                                confvalue = False
                            elif str(confvalue).lower() in ["true"]:
                                confvalue = True
                            updatedict[key] = confvalue
                        elif key in ["favorite", "HD"]:
                            updatedict[key] = int(channel[key])
                    else:
                        channel_id = str(channel[key])
                self.fhdhr.device.channels.set_channel_status("id", channel_id, updatedict, origin)

        elif method == "scan":
            self.fhdhr.device.channels.get_channels(forceupdate=True, origin=origin)

        else:
            return "Invalid Method"

        if redirect_url:
            return redirect("%s?retmessage=%s" % (redirect_url, urllib.parse.quote("%s Success" % method)))
        else:
            if method == "scan":
                return redirect('/lineup_status.json')
            else:
                return "%s Success" % method
