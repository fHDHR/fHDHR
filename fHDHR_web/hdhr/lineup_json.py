from flask import Response, request
import json

from fHDHR.tools import channel_sort


class Lineup_JSON():
    endpoints = ["/lineup.json", "/hdhr/lineup.json"]
    endpoint_name = "hdhr_lineup_json"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        base_url = request.url_root[:-1]

        show = request.args.get('show', default="all", type=str)

        channelslist = {}
        for fhdhr_id in [x["id"] for x in self.fhdhr.device.channels.get_channels()]:
            channel_obj = self.fhdhr.device.channels.list[fhdhr_id]
            if channel_obj.enabled or show == "found":
                lineup_dict = channel_obj.lineup_dict
                lineup_dict["URL"] = "%s%s" % (base_url, lineup_dict["URL"])
                if show == "found" and channel_obj.enabled:
                    lineup_dict["Enabled"] = 1
                elif show == "found" and not channel_obj.enabled:
                    lineup_dict["Enabled"] = 0

            channelslist[channel_obj.number] = lineup_dict

        # Sort the channels
        sorted_channel_list = channel_sort(list(channelslist.keys()))
        sorted_chan_guide = []
        for channel in sorted_channel_list:
            sorted_chan_guide.append(channelslist[channel])

        lineup_json = json.dumps(sorted_chan_guide, indent=4)

        return Response(status=200,
                        response=lineup_json,
                        mimetype='application/json')
