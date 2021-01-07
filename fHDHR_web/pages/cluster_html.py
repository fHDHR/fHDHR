from flask import request, render_template, session
import urllib.parse


class Cluster_HTML():
    endpoints = ["/cluster", "/cluster.html"]
    endpoint_name = "page_cluster_html"
    endpoint_access_level = 1
    pretty_name = "Cluster/SSDP"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr
        self.location_dict = {
                              "name": self.fhdhr.config.dict["fhdhr"]["friendlyname"],
                              "location": self.fhdhr.api.base,
                              "joined": "N/A",
                              "url_query": self.fhdhr.api.base_quoted
                              }

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        locations_list = []

        if self.fhdhr.config.dict["fhdhr"]["discovery_address"]:

            locations_list.append(self.location_dict)

            fhdhr_list = self.fhdhr.device.cluster.get_list()
            for location in list(fhdhr_list.keys()):

                if location in list(self.fhdhr.device.cluster.cluster().keys()):
                    location_name = self.fhdhr.device.cluster.cluster()[location]["name"]
                else:
                    try:
                        location_info_url = location + "/discover.json"
                        location_info_req = self.fhdhr.web.session.get(location_info_url)
                        location_info = location_info_req.json()
                        location_name = location_info["FriendlyName"]
                    except self.fhdhr.web.exceptions.ConnectionError:
                        self.fhdhr.logger.error("Unreachable: " + location)
                location_dict = {
                                "name": location_name,
                                "location": location,
                                "joined": str(fhdhr_list[location]["Joined"]),
                                "url_query": urllib.parse.quote(location)
                                }
                locations_list.append(location_dict)

        return render_template('cluster.html', session=session, request=request, fhdhr=self.fhdhr, locations_list=locations_list)
