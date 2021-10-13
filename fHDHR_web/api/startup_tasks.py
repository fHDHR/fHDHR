

class Startup_Tasks():
    endpoints = ["/api/startup_tasks"]
    endpoint_name = "api_startup_tasks"
    endpoint_methods = ["GET", "POST"]

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

        self.epg_update_url = "/api/epg?method=update"
        self.channel_update_url = "/api/channels?method=scan"

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        self.fhdhr.logger.noob("Running Startup Tasks.")

        tags_list = self.fhdhr.scheduler.list_tags()

        self.startup_versions_update(tags_list)

        self.startup_channel_scan(tags_list)

        self.startup_epg_update(tags_list)

        self.startup_ssdp_alive(tags_list)

        self.fhdhr.logger.noob("Startup Tasks Complete.")

        return "Success"

    def startup_epg_update(self, tags_list):

        for epg_method in self.fhdhr.device.epg.epg_methods:
            haseverpulled = self.fhdhr.db.get_fhdhr_value("epg", "update_time", epg_method)
            updateepg = False

            if hasattr(self.fhdhr.device.epg.epg_methods[epg_method]["class"], "epg_update_on_start"):
                updateepg = self.fhdhr.device.epg.epg_methods[epg_method]["class"].epg_update_on_start

            elif epg_method in list(self.fhdhr.config.dict.keys()):
                if "epg_update_on_start" in list(self.fhdhr.config.dict[epg_method].keys()):
                    updateepg = self.fhdhr.config.dict[epg_method]["epg_update_on_start"]
                else:
                    updateepg = self.fhdhr.config.dict["fhdhr"]["epg_update_on_start"]

            elif self.fhdhr.config.dict["epg"]["epg_update_on_start"]:
                updateepg = self.fhdhr.config.dict["epg"]["epg_update_on_start"]

            elif haseverpulled:
                updateepg = False

            if updateepg:
                if ("%s EPG Update" % epg_method) in tags_list:
                    self.fhdhr.scheduler.run_from_tag("%s EPG Update" % epg_method)

    def startup_channel_scan(self, tags_list):
        for origin in list(self.fhdhr.origins.origins_dict.keys()):

            haseverscanned = self.fhdhr.db.get_fhdhr_value("channels", "scanned_time", origin)
            updatechannels = False

            if hasattr(self.fhdhr.origins.origins_dict[origin], "chanscan_on_start"):
                updatechannels = self.fhdhr.origins.origins_dict[origin].chanscan_on_start

            elif origin in list(self.fhdhr.config.dict.keys()):
                if "chanscan_on_start" in list(self.fhdhr.config.dict[origin].keys()):
                    updatechannels = self.fhdhr.config.dict[origin]["chanscan_on_start"]
                else:
                    updatechannels = self.fhdhr.config.dict["fhdhr"]["chanscan_on_start"]

            elif self.fhdhr.config.dict["fhdhr"]["chanscan_on_start"]:
                updatechannels = self.fhdhr.config.dict["fhdhr"]["chanscan_on_start"]

            elif haseverscanned:
                updatechannels = False

            if updatechannels:
                if ("%s Channel Scan" % origin) in tags_list:
                    self.fhdhr.scheduler.run_from_tag("%s Channel Scan" % origin)

    def startup_versions_update(self, tags_list):
        if "Versions Update" in tags_list:
            self.fhdhr.scheduler.run_from_tag("Versions Update")

    def startup_ssdp_alive(self, tags_list):
        if "SSDP Alive" in tags_list:
            self.fhdhr.scheduler.run_from_tag("SSDP Alive")
