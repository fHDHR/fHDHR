from flask import request, render_template, session
import datetime

from fHDHR.tools import humanized_time, channel_sort


class Guide_HTML():
    endpoints = ["/guide", "/guide.html"]
    endpoint_name = "page_guide_html"
    endpoint_access_level = 0
    pretty_name = "Guide"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        nowtime = datetime.datetime.utcnow().timestamp()

        chan_guide_list = []

        source = request.args.get('source', default=self.fhdhr.device.epg.def_method, type=str)
        epg_methods = self.fhdhr.device.epg.valid_epg_methods
        if source not in epg_methods:
            source = self.fhdhr.device.epg.def_method

        if not source:
            return render_template('guide.html', request=request, session=session, fhdhr=self.fhdhr, chan_guide_list=chan_guide_list, epg_methods=epg_methods, source=source, list=list)

        whatson = self.fhdhr.device.epg.whats_on_allchans(source)

        # Sort the channels
        sorted_channel_list = channel_sort(list(whatson.keys()))
        sorted_chan_guide = {}
        for channel in sorted_channel_list:
            sorted_chan_guide[channel] = whatson[channel]

        for channel in list(sorted_chan_guide.keys()):
            if sorted_chan_guide[channel]["listing"][0]["time_end"]:
                remaining_time = humanized_time(sorted_chan_guide[channel]["listing"][0]["time_end"] - nowtime)
            else:
                remaining_time = "N/A"

            chan_dict = {
                         "name": sorted_chan_guide[channel]["name"],
                         "number": sorted_chan_guide[channel]["number"],
                         "chan_thumbnail": sorted_chan_guide[channel]["thumbnail"],
                         "listing_title": sorted_chan_guide[channel]["listing"][0]["title"],
                         "listing_thumbnail": sorted_chan_guide[channel]["listing"][0]["thumbnail"],
                         "listing_description": sorted_chan_guide[channel]["listing"][0]["description"],
                         "listing_remaining_time": str(remaining_time)
                         }

            for time_item in ["time_start", "time_end"]:

                if not sorted_chan_guide[channel]["listing"][0][time_item]:
                    chan_dict["listing_%s" % time_item] = "N/A"
                elif str(sorted_chan_guide[channel]["listing"][0][time_item]).endswith(tuple(["+0000", "+00:00"])):
                    chan_dict["listing_%s" % time_item] = str(sorted_chan_guide[channel]["listing"][0][time_item])
                else:
                    chan_dict["listing_%s" % time_item] = str(datetime.datetime.fromtimestamp(sorted_chan_guide[channel]["listing"][0][time_item]))

            if source in self.fhdhr.origins.valid_origins:
                chan_obj = self.fhdhr.device.channels.get_channel_obj("origin_id", sorted_chan_guide[channel]["id"], source)

                chan_dict["name"] = chan_obj.dict["name"]
                chan_dict["number"] = chan_obj.number
                chan_dict["chan_thumbnail"] = chan_obj.thumbnail
                chan_dict["enabled"] = chan_obj.dict["enabled"]
                chan_dict["m3u_url"] = chan_obj.api_m3u_url

                chan_dict["listing_thumbnail"] = chan_dict["listing_thumbnail"] or chan_obj.thumbnail
            else:
                if not chan_dict["listing_thumbnail"]:
                    chan_dict["listing_thumbnail"] = chan_dict["chan_thumbnail"]
                if not chan_dict["listing_thumbnail"]:
                    chan_dict["listing_thumbnail"] = "/api/images?method=generate&type=channel&message=%s" % chan_dict["number"]

            chan_guide_list.append(chan_dict)

        return render_template('guide.html', request=request, session=session, fhdhr=self.fhdhr, chan_guide_list=chan_guide_list, epg_methods=epg_methods, source=source, list=list)
