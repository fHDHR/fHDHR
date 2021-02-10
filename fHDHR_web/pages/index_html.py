from flask import request, render_template, session


class Index_HTML():
    endpoints = ["/index", "/index.html"]
    endpoint_name = "page_index_html"
    endpoint_access_level = 0
    pretty_name = "Index"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        channel_counts = [len(list(self.fhdhr.device.channels.list[origin].keys())) for origin in list(self.fhdhr.device.channels.list.keys())]

        fhdhr_status_dict = {
                            "Script Directory": str(self.fhdhr.config.internal["paths"]["script_dir"]),
                            "Config File": str(self.fhdhr.config.config_file),
                            "Cache Path": str(self.fhdhr.config.internal["paths"]["cache_dir"]),
                            "Database Type": self.fhdhr.config.dict["database"]["type"],
                            "Logging Level": self.fhdhr.config.dict["logging"]["level"],
                            }

        fhdhr_status_dict["Total Plugins"] = len(list(self.fhdhr.plugins.plugins.keys()))
        if self.fhdhr.config.internal["paths"]["external_plugins_dir"]:
            fhdhr_status_dict["Plugins Path"] = ", ".join([
             str(self.fhdhr.config.internal["paths"]["internal_plugins_dir"]),
             str(self.fhdhr.config.internal["paths"]["external_plugins_dir"])
             ])
        else:
            fhdhr_status_dict["Plugins Path"] = str(self.fhdhr.config.internal["paths"]["internal_plugins_dir"])

        fhdhr_status_dict["Channels"] = "%s from %s origins. Avg %s/origin" % (sum(channel_counts), len(channel_counts), int(sum(channel_counts) / len(channel_counts)))
        for origin in list(self.fhdhr.device.channels.list.keys()):
            tuners_in_use = self.fhdhr.device.tuners.inuse_tuner_count(origin)
            max_tuners = self.fhdhr.origins.origins_dict[origin].tuners
            fhdhr_status_dict["%s Channel Count" % origin] = len(list(self.fhdhr.device.channels.list[origin].keys()))
            fhdhr_status_dict["%s Tuner Usage" % origin] = "%s/%s" % (str(tuners_in_use), str(max_tuners))

        fhdhr_status_dict["EPG Methods That Update"] = ", ".join(self.fhdhr.device.epg.epg_methods)

        return render_template('index.html', request=request, session=session, fhdhr=self.fhdhr, fhdhr_status_dict=fhdhr_status_dict, list=list)
