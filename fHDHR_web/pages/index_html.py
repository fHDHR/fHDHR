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

        total_channels = 0
        for origin in list(self.fhdhr.device.channels.list.keys()):
            total_channels += len(list(self.fhdhr.device.channels.list[origin].keys()))

        fhdhr_status_dict = {
                            "Script Directory": str(self.fhdhr.config.internal["paths"]["script_dir"]),
                            "Config File": str(self.fhdhr.config.config_file),
                            "Cache Path": str(self.fhdhr.config.internal["paths"]["cache_dir"]),
                            "Total Channels": total_channels,
                            }

        return render_template('index.html', request=request, session=session, fhdhr=self.fhdhr, fhdhr_status_dict=fhdhr_status_dict, list=list)
