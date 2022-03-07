from flask import request, redirect
import urllib.parse

from fHDHR_web.tools import api_sub_handler, tabbed_json_response


class Origins():
    endpoints = ["/api/origins"]
    endpoint_name = "api_origins"
    endpoint_methods = ["GET", "POST"]
    endpoint_parameters = {
                            "method": {
                                    "default": "get",
                                    "valid_options": ["get", "list", "count", "scan"]
                                    },
                            "origin": {
                                    "default": None,
                                    "valid_options": "origins"
                                    }
                            }

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return api_sub_handler(self, *args)

    def handler(self, parameters, *args):

        redirect_url = request.args.get('redirect', default=None, type=str)

        method = parameters["method"]

        if method == "get":
            return self.get(request, parameters)

        if method == "scan":
            return self.scan(parameters)

        if method == "list":
            return self.list()

        if method == "count":
            return self.count()

        if redirect_url:
            if "?" in redirect_url:
                return redirect("%s&retmessage=%s" % (redirect_url, urllib.parse.quote("%s Success" % method)))
            else:
                return redirect("%s?retmessage=%s" % (redirect_url, urllib.parse.quote("%s Success" % method)))
        else:
            return "%s Success" % method

    def get(self, request, parameters):

        origin_name = parameters["origin"]

        origins_dict = {}

        origins_info = {}
        if not origin_name:
            origins_list = self.fhdhr.origins.list_origins
        else:
            origins_list = [origin_name]

        if len(origins_list) > 1:
            origins_dict.update({
                                 "count_origins": self.fhdhr.origins.count_origins,
                                 "list_origins": self.fhdhr.origins.list_origins
                                 })

        for origin_name_item in origins_list:

            origins_info[origin_name_item] = {}
            origin_obj = self.fhdhr.origins.get_origin_obj(origin_name_item)

            # Display Configuration options
            origins_info[origin_name_item].update(origin_obj.get_origin_conf())

            # Show Total Channels
            origins_info[origin_name_item].update({
                                                   "setup_success": origin_obj.setup_success,
                                                   "channel_count": origin_obj.count_channels
                                                   })

            # Show when the scheduler is set to run
            schedule_dict = origin_obj.get_scheduled_time()
            origins_info[origin_name_item].update({
                                                   "schedule_name": schedule_dict["name"],
                                                   "schedule_last_run": str(schedule_dict["last_run"]),
                                                   "schedule_next_run": str(schedule_dict["next_run"])
                                                   })

            # Show if origin has a method
            has_method_dict = {}
            has_method_list_check = ["prime_stream", "close_stream", "webpage_dict"]
            for origin_attr in has_method_list_check:
                has_method_dict[origin_attr] = origin_obj.has_method(origin_attr)
            origins_info[origin_name_item].update({"has_methods": has_method_dict})

            # List Channels in Origins API
            channels_info = {}
            sorted_channel_dicts = origin_obj.sorted_channel_dicts
            for channel_dict in sorted_channel_dicts:
                fhdhr_channel_id = channel_dict["id"]
                channel_obj = origin_obj.get_channel_obj(fhdhr_channel_id)
                channels_info[channel_obj.number] = channel_dict
                channels_info[channel_obj.number].update({"m3u_url": channel_obj.api_m3u_url,
                                                          "w3u_url": channel_obj.api_w3u_url,
                                                          "stream_url": channel_obj.api_stream_url
                                                          })
            origins_info[origin_name_item]["channels"] = channels_info

        origins_dict.update({"origins": origins_info})

        return tabbed_json_response(origins_dict)

    def scan(self, request, parameters):

        origin_name = parameters["origin"]

        if not origin_name:
            origins_list = self.fhdhr.origins.list_origins
        else:
            origins_list = [origin_name]

        for origin_name_item in origins_list:
            self.fhdhr.origins.run_schedule_scan()

    def list(self):
        origins_dict = {}
        origins_dict.update({
                             "list_origins": self.fhdhr.origins.list_origins
                             })
        return tabbed_json_response(origins_dict)

    def count(self):
        origins_dict = {}
        origins_dict.update({
                             "count_origins": self.fhdhr.origins.count_origins
                             })
        return tabbed_json_response(origins_dict)
