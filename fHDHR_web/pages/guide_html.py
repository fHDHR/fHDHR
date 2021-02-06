from flask import request, session, render_template
import datetime

from fHDHR.tools import channel_sort, humanized_time


class Guide_HTML():
    endpoints = ["/guide", "/guide.html"]
    endpoint_name = "page_guide_html"
    endpoint_access_level = 0
    pretty_name = "Guide"
    endpoint_category = "pages"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        nowtime = datetime.datetime.utcnow().timestamp()

        source = request.args.get('source', default=self.fhdhr.device.epg.def_method, type=str)
        epg_methods = self.fhdhr.device.epg.valid_epg_methods
        if source not in epg_methods:
            source = self.fhdhr.device.epg.def_method

        origin_methods = self.fhdhr.origins.valid_origins

        channelslist = {}

        if not source:
            return render_template('guide.html', request=request, session=session, fhdhr=self.fhdhr, channelslist=channelslist, epg_methods=epg_methods, origin=source, origin_methods=origin_methods, list=list)

        whatson_all = self.fhdhr.device.epg.whats_on_allchans(source)

        if source in origin_methods:

            sorted_channel_list = channel_sort([self.fhdhr.device.channels.list[source][x].number for x in list(self.fhdhr.device.channels.list[source].keys())])
            for channel in sorted_channel_list:

                channel_obj = self.fhdhr.device.channels.get_channel_obj("number", channel, source)
                channel_dict = channel_obj.dict.copy()

                now_playing = whatson_all[channel]

                channel_dict["number"] = channel_obj.number
                channel_dict["chan_thumbnail"] = channel_obj.thumbnail
                channel_dict["m3u_url"] = channel_obj.api_m3u_url

                current_listing = now_playing["listing"][0]

                channel_dict["listing_title"] = current_listing["title"]
                channel_dict["listing_thumbnail"] = current_listing["thumbnail"]
                channel_dict["listing_description"] = current_listing["description"]

                if current_listing["time_end"]:
                    channel_dict["listing_remaining_time"] = humanized_time(current_listing["time_end"] - nowtime)
                else:
                    channel_dict["listing_remaining_time"] = "N/A"

                for time_item in ["time_start", "time_end"]:

                    if not current_listing[time_item]:
                        channel_dict["listing_%s" % time_item] = "N/A"
                    elif str(current_listing[time_item]).endswith(tuple(["+0000", "+00:00"])):
                        channel_dict["listing_%s" % time_item] = str(current_listing[time_item])
                    else:
                        channel_dict["listing_%s" % time_item] = str(datetime.datetime.fromtimestamp(current_listing[time_item]))

                channelslist[channel_obj.number] = channel_dict

        elif source in epg_methods:
            sorted_channel_list = channel_sort([x for x in list(whatson_all.keys())])

            for channel in sorted_channel_list:

                channel_dict = {
                                "name": whatson_all[channel]["name"],
                                "number": whatson_all[channel]["number"],
                                "chan_thumbnail": whatson_all[channel]["thumbnail"],
                                }

                now_playing = whatson_all[channel]

                current_listing = now_playing["listing"][0]

                channel_dict["listing_title"] = current_listing["title"]
                channel_dict["listing_thumbnail"] = current_listing["thumbnail"]
                channel_dict["listing_description"] = current_listing["description"]

                if current_listing["time_end"]:
                    channel_dict["listing_remaining_time"] = humanized_time(current_listing["time_end"] - nowtime)
                else:
                    channel_dict["listing_remaining_time"] = "N/A"

                for time_item in ["time_start", "time_end"]:

                    if not current_listing[time_item]:
                        channel_dict["listing_%s" % time_item] = "N/A"
                    elif str(current_listing[time_item]).endswith(tuple(["+0000", "+00:00"])):
                        channel_dict["listing_%s" % time_item] = str(current_listing[time_item])
                    else:
                        channel_dict["listing_%s" % time_item] = str(datetime.datetime.fromtimestamp(current_listing[time_item]))

                channelslist[channel] = channel_dict

        return render_template('guide.html', request=request, session=session, fhdhr=self.fhdhr, channelslist=channelslist, epg_methods=epg_methods, origin=source, origin_methods=origin_methods, list=list)
