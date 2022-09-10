from flask import Response, request, redirect
import urllib.parse
import json
import datetime

from fHDHR.tools import channel_sort


class EPG():
    """Methods to create xmltv.xml"""
    endpoints = ["/api/epg"]
    endpoint_name = "api_epg"
    endpoint_methods = ["GET", "POST"]

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.handler(*args)

    def handler(self, *args):

        method = request.args.get('method', default="get", type=str)
        source = request.args.get('source', default=self.fhdhr.device.epg.def_method, type=str)
        if source not in self.fhdhr.device.epg.valid_epg_methods:
            return "%s Invalid epg method" % source

        redirect_url = request.args.get('redirect', default=None, type=str)

        if method == "get":

            epgdict = self.fhdhr.device.epg.get_epg(source)

            # Sort the channels
            sorted_channel_list = channel_sort(list(epgdict.keys()))
            sorted_chan_guide = {}
            for channel in sorted_channel_list:
                sorted_chan_guide[channel] = epgdict[channel]

            epg_json = json.dumps(sorted_chan_guide, indent=4)

            return Response(status=200,
                            response=epg_json,
                            mimetype='application/json')

        elif method == "current":

            nowtime = datetime.datetime.utcnow().timestamp()

            chan_guide_list = []

            whatson = self.fhdhr.device.epg.whats_on_allchans(source)

            # Sort the channels
            sorted_channel_list = channel_sort(list(whatson.keys()))
            sorted_chan_guide = {}
            for channel in sorted_channel_list:
                sorted_chan_guide[channel] = whatson[channel]

            for channel in list(sorted_chan_guide.keys()):
                if sorted_chan_guide[channel]["listing"][0]["time_end"]:
                    remaining_time = self.fhdhr.time.humanized_time(sorted_chan_guide[channel]["listing"][0]["time_end"] - nowtime)
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

                if not chan_dict["listing_thumbnail"]:
                    chan_dict["listing_thumbnail"] = chan_dict["chan_thumbnail"]
                if not chan_dict["listing_thumbnail"]:
                    chan_dict["listing_thumbnail"] = "/api/images?method=generate&type=channel&message=%s" % chan_dict["number"]

                chan_guide_list.append(chan_dict)

            epg_json = json.dumps(chan_guide_list, indent=4)

            return Response(status=200,
                            response=epg_json,
                            mimetype='application/json')

        elif method == "update":
            tags_list = self.fhdhr.scheduler.list_tags
            if ("%s EPG Update" % source) not in tags_list:
                self.fhdhr.device.epg.update(source)
            else:
                self.fhdhr.scheduler.run_from_tag("%s EPG Update" % source)

        elif method == "map":
            channels_list = json.loads(request.form.get('channels', []))
            for channel in channels_list:
                if channel["fhdhr_channel_id"] in [None, "None"]:
                    self.fhdhr.device.epg.unset_epg_chan_match(channel["epg_method"], channel["id"])
                else:
                    chan_obj = None
                    if "fhdhr_channel_id" in channel:
                        chan_obj = self.fhdhr.origins.origins_dict[source].find_channel_obj(channel["fhdhr_channel_id"], searchkey="id")
                    if chan_obj is not None:
                        self.fhdhr.device.epg.set_epg_chan_match(channel["epg_method"], channel["id"], channel["fhdhr_channel_id"], chan_obj.origin_name)

        elif method == "clearcache":
            self.fhdhr.device.epg.clear_epg_cache(source)

        else:
            return "%s Invalid Method" % method

        if redirect_url:
            if "?" in redirect_url:
                return redirect("%s&retmessage=%s" % (redirect_url, urllib.parse.quote("%s Success" % method)))
            else:
                return redirect("%s?retmessage=%s" % (redirect_url, urllib.parse.quote("%s Success" % method)))
        else:
            return "%s Success" % method
