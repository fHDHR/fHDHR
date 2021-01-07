from flask import request, render_template, session

from fHDHR.tools import channel_sort


class Channels_HTML():
    endpoints = ["/channels", "/channels.html"]
    endpoint_name = "page_channels_html"
    endpoint_access_level = 0
    pretty_name = "Channels"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        channels_dict = {
                        "Total Channels": len(self.fhdhr.device.channels.get_channels()),
                        "Enabled": 0
                        }

        channelslist = {}
        for fhdhr_id in [x["id"] for x in self.fhdhr.device.channels.get_channels()]:
            channel_obj = self.fhdhr.device.channels.list[fhdhr_id]
            channel_dict = channel_obj.dict.copy()

            channel_dict["number"] = channel_obj.number
            channel_dict["chan_thumbnail"] = channel_obj.thumbnail
            channel_dict["play_url"] = channel_obj.play_url

            channelslist[channel_dict["number"]] = channel_dict
            if channel_dict["enabled"]:
                channels_dict["Enabled"] += 1

        # Sort the channels
        sorted_channel_list = channel_sort(list(channelslist.keys()))
        sorted_chan_guide = []
        for channel in sorted_channel_list:
            sorted_chan_guide.append(channelslist[channel])

        return render_template('channels.html', session=session, request=request, fhdhr=self.fhdhr, channelslist=sorted_chan_guide, channels_dict=channels_dict, list=list)
