from flask import request, redirect, Response, abort
import urllib.parse
import json

from fHDHR.tools import channel_sort


class Channels():
    endpoints = ["/api/channels"]
    endpoint_name = "api_channels"
    endpoint_methods = ["GET", "POST"]
    endpoint_parameters = {
                            "method": {
                                    "default": "get"
                                    }
                            }

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.handler(*args)

    def handler(self, *args):

        method = request.args.get('method', default=None, type=str)
        redirect_url = request.args.get('redirect', default=None, type=str)

        origin_methods = self.fhdhr.origins.list_origins
        origin_name = request.args.get('origin', default=None, type=str)
        if origin_name and origin_name not in origin_methods:
            return "%s Invalid channels origin" % origin_name

        if method == "get":
            channels_info = {}
            if not origin_name:
                origin_list = origin_methods
            else:
                origin_list = [origin_name]

            for origin_name in origin_list:

                channels_info[origin_name] = {}

                for fhdhr_channel_id in self.fhdhr.origins.origins_dict[origin_name].channels.list_channel_ids:
                    channel_obj = self.fhdhr.origins.origins_dict[origin_name].channels.channel_list[fhdhr_channel_id]
                    if channel_obj:
                        channel_dict = channel_obj.dict.copy()
                        channel_dict["m3u_url"] = channel_obj.api_m3u_url
                        channel_dict["stream_url"] = channel_obj.api_stream_url
                        channels_info[origin_name][channel_obj.number] = channel_dict

                # Sort the channels
                sorted_channel_list = channel_sort(list(channels_info[origin_name].keys()))
                sorted_chan_guide = []
                for channel in sorted_channel_list:
                    sorted_chan_guide.append(channels_info[origin_name][channel])

                channels_info[origin_name] = sorted_chan_guide

            channels_info_json = json.dumps(channels_info, indent=4)

            return Response(status=200,
                            response=channels_info_json,
                            mimetype='application/json')

        elif method == "favorite":

            channel = request.args.get('channel', default=None, type=str)
            if not channel:
                if redirect_url:
                    if "?" in redirect_url:
                        return redirect("%s&retmessage=%s" % (redirect_url, urllib.parse.quote("%s Failed" % method)))
                    else:
                        return redirect("%s?retmessage=%s" % (redirect_url, urllib.parse.quote("%s Failed" % method)))
                else:
                    return "%s Falied" % method

            if channel.startstwith(tuple(["+", "-", "x"])):

                channel_method = channel[0]
                channel_number = channel[1:]

                if str(channel_number) not in [str(x) for x in self.fhdhr.origins.origins_dict[origin_name].channels.create_channel_list("number")]:
                    response = Response("Not Found", status=404)
                    response.headers["X-fHDHR-Error"] = "801 - Unknown Channel"
                    self.fhdhr.logger.error(response.headers["X-fHDHR-Error"])
                    abort(response)

                if channel_method == "+":
                    self.fhdhr.origins.origins_dict[origin_name].channels.set_channel_enablement(channel_number, channel_method, "number")
                elif channel_method == "-":
                    self.fhdhr.origins.origins_dict[origin_name].channels.set_channel_enablement(channel_number, channel_method, "number")
                elif channel_method == "x":
                    self.fhdhr.origins.origins_dict[origin_name].channels.set_channel_enablement(channel_number, "toggle", "number")

            else:
                self.fhdhr.logger.warning("Unknown favorite command %s" % request.args['favorite'])
                return abort(200, "Not a valid favorite command")

        elif method in ["enable", "disable"]:
            channel = request.args.get('channel', default=None, type=str)
            if channel == "all":
                self.fhdhr.origins.origins_dict[origin_name].channels.set_channel_enablement_all(method)
            elif not channel or str(channel) not in [str(x) for x in self.fhdhr.origins.origins_dict[origin_name].channels.create_channel_list("number")]:
                if redirect_url:
                    if "?" in redirect_url:
                        return redirect("%s&retmessage=%s" % (redirect_url, urllib.parse.quote("%s Failed" % method)))
                    else:
                        return redirect("%s?retmessage=%s" % (redirect_url, urllib.parse.quote("%s Failed" % method)))
                else:
                    return "%s Falied" % method
            else:
                self.fhdhr.origins.origins_dict[origin_name].channels.set_channel_enablement(channel, method, "id")

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
            self.fhdhr.origins.origins_dict[origin_name].channels.set_channel_status(channel_id, updatedict, "id")

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
                self.fhdhr.origins.origins_dict[origin_name].channels.set_channel_status(channel_id, updatedict, "id")

        elif method == "scan":
            self.fhdhr.origins.origins_dict[origin_name].channels.run_schedule_scan()

        elif method == "delete":
            fhdhr_channel_id = request.args.get('fhdhr_channel_id', default=None, type=str)
            if fhdhr_channel_id:
                self.fhdhr.origins.origins_dict[origin_name].channels.delete_channel(fhdhr_channel_id)
                self.fhdhr.device.epg.delete_channel(fhdhr_channel_id, origin_name)

        else:
            return "Invalid Method"

        if redirect_url:
            if "?" in redirect_url:
                return redirect("%s&retmessage=%s" % (redirect_url, urllib.parse.quote("%s Success" % method)))
            else:
                return redirect("%s?retmessage=%s" % (redirect_url, urllib.parse.quote("%s Success" % method)))
        else:
            if method == "scan":
                return redirect('/lineup_status.json')
            else:
                return "%s Success" % method
