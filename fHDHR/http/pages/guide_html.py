from flask import request, render_template
import datetime

from fHDHR.tools import humanized_time


class Guide_HTML():
    endpoints = ["/guide", "/guide.html"]
    endpoint_name = "page_guide_html"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        nowtime = datetime.datetime.utcnow()

        chan_guide_list = []

        source = request.args.get('source', default=self.fhdhr.device.epg.def_method, type=str)
        epg_methods = self.fhdhr.device.epg.valid_epg_methods
        if source not in epg_methods:
            source = self.fhdhr.device.epg.def_method

        for channel in self.fhdhr.device.epg.whats_on_allchans(source):
            end_time = datetime.datetime.strptime(channel["listing"][0]["time_end"], '%Y%m%d%H%M%S +0000')
            remaining_time = humanized_time(int((end_time - nowtime).total_seconds()))

            chan_dict = {
                         "name": channel["name"],
                         "number": channel["number"],
                         "chan_thumbnail": channel["thumbnail"],
                         "listing_title": channel["listing"][0]["title"],
                         "listing_thumbnail": channel["listing"][0]["thumbnail"],
                         "listing_description": channel["listing"][0]["description"],
                         "remaining_time": str(remaining_time)
                         }
            chan_guide_list.append(chan_dict)

        return render_template('guide.html', request=request, fhdhr=self.fhdhr, chan_guide_list=chan_guide_list, epg_methods=epg_methods)
