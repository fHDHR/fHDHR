

class Startup_Tasks():
    endpoints = ["/api/startup_tasks"]
    endpoint_name = "api_startup_tasks"
    endpoint_methods = ["GET", "POST"]

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

        self.epg_update_url = "%s/api/epg?method=update" % (self.fhdhr.api.base)
        self.channel_update_url = "%s/api/channels?method=scan" % (self.fhdhr.api.base)

    def __call__(self, *args):
        return self.get(*args)

    def get(self, *args):

        # Hit Channel Update API URL without waiting unless we've never scanned before
        haseverscanned = self.fhdhr.db.get_fhdhr_value("channels", "scanned_time")
        if not haseverscanned:
            self.fhdhr.web.session.get(self.channel_update_url)
        elif self.fhdhr.config.dict["fhdhr"]["chanscan_on_start"]:
            try:
                self.fhdhr.web.session.get(self.channel_update_url, timeout=0.0000000001)
            except self.fhdhr.web.exceptions.ReadTimeout:
                pass

        # Hit EPG Update API URL without waiting
        try:
            self.fhdhr.web.session.get(self.epg_update_url, timeout=0.0000000001)
        except self.fhdhr.web.exceptions.ReadTimeout:
            pass

        return "Success"
