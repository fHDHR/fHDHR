from flask import request, render_template


class Index_HTML():
    endpoints = ["/", "/index", "/index.html"]
    endpoint_name = "root"

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        tuners_in_use = self.fhdhr.device.tuners.inuse_tuner_count()
        max_tuners = self.fhdhr.device.tuners.max_tuners

        fhdhr_status_dict = {
                            "Script Directory": str(self.fhdhr.config.internal["paths"]["script_dir"]),
                            "Config File": str(self.fhdhr.config.config_file),
                            "Cache Path": str(self.fhdhr.config.internal["paths"]["cache_dir"]),
                            "Total Channels": str(self.fhdhr.device.channels.get_station_total()),
                            "Tuner Usage": ("%s/%s" % (str(tuners_in_use), str(max_tuners))),
                            }

        return render_template('index.html', request=request, fhdhr=self.fhdhr, fhdhr_status_dict=fhdhr_status_dict, list=list)
