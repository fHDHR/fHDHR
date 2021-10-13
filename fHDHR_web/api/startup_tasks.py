

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

        # Hit Channel Update API
        for origin in list(self.fhdhr.origins.origins_dict.keys()):

            haseverscanned = self.fhdhr.db.get_fhdhr_value("channels", "scanned_time", origin)
            updatechannels = False

            if not haseverscanned:
                updatechannels = True

            elif hasattr(self.fhdhr.origins.origins_dict[origin], "chanscan_on_start"):
                updatechannels = self.fhdhr.origins.origins_dict[origin].chanscan_on_start

            elif origin in list(self.fhdhr.config.dict.keys()):
                if "chanscan_on_start" in list(self.fhdhr.config.dict[origin].keys()):
                    updatechannels = self.fhdhr.config.dict[origin]["chanscan_on_start"]
                else:
                    updatechannels = self.fhdhr.config.dict["fhdhr"]["chanscan_on_start"]

            elif self.fhdhr.config.dict["fhdhr"]["chanscan_on_start"]:
                updatechannels = self.fhdhr.config.dict["fhdhr"]["chanscan_on_start"]

            if updatechannels:
                self.fhdhr.api.get("%s&origin=%s" % (self.channel_update_url, origin))

        # Hit EPG Update API
        for epg_method in self.fhdhr.device.epg.epg_methods:
            haseverpulled = self.fhdhr.db.get_fhdhr_value("epg", "update_time", epg_method)
            updateepg = False

            if not haseverpulled:
                updateepg = True

            elif hasattr(self.fhdhr.device.epg.epg_methods[epg_method]["class"], "epg_update_on_start"):
                updateepg = self.fhdhr.device.epg.epg_methods[epg_method]["class"].epg_update_on_start

            elif epg_method in list(self.fhdhr.config.dict.keys()):
                if "epg_update_on_start" in list(self.fhdhr.config.dict[epg_method].keys()):
                    updateepg = self.fhdhr.config.dict[epg_method]["epg_update_on_start"]
                else:
                    updateepg = self.fhdhr.config.dict["fhdhr"]["epg_update_on_start"]

            elif self.fhdhr.config.dict["epg"]["epg_update_on_start"]:
                updateepg = True

            if updateepg:
                self.fhdhr.api.get("%s&source=%s" % (self.epg_update_url, epg_method))

        self.fhdhr.logger.noob("Startup Tasks Complete.")

        return "Success"
