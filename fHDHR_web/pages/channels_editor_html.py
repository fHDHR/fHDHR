from flask import request, render_template, session

from fHDHR.tools import channel_sort


class Channels_Editor_HTML():
    endpoints = ["/channels_editor", "/channels_editor.html"]
    endpoint_name = "page_channels_editor_html"
    endpoint_access_level = 2
    endpoint_category = "tool_pages"
    pretty_name = "Channels Editor"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        origin_methods = self.fhdhr.origins.valid_origins
        if len(self.fhdhr.origins.valid_origins):

            origin = request.args.get('origin', default=self.fhdhr.origins.valid_origins[0], type=str)
            if origin not in origin_methods:
                origin = origin_methods[0]

            channelslist = {}
            for fhdhr_id in [x["id"] for x in self.fhdhr.device.channels.get_channels(origin)]:
                channel_obj = self.fhdhr.device.channels.find_channel_obj(fhdhr_id, searchkey="id", origin=origin)
                if channel_obj:
                    channel_dict = channel_obj.dict.copy()

                    channel_dict["number"] = channel_obj.number
                    channel_dict["chan_thumbnail"] = channel_obj.thumbnail
                    channel_dict["m3u_url"] = channel_obj.api_m3u_url

                    channelslist[channel_dict["number"]] = channel_dict

            # Sort the channels
            sorted_channel_list = channel_sort(list(channelslist.keys()))
            sorted_chan_guide = []
            for channel in sorted_channel_list:
                sorted_chan_guide.append(channelslist[channel])
        else:
            origin = None
            sorted_chan_guide = []

        return render_template('channels_editor.html', request=request, session=session, fhdhr=self.fhdhr, channelslist=sorted_chan_guide, origin=origin, origin_methods=origin_methods, list=list)
