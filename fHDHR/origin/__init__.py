from .origin_service import OriginService
from .origin_channels import OriginChannels
from .origin_epg import OriginEPG

import fHDHR.exceptions


class OriginEPG_StandIN():
    def __init__(self):
        pass

    def update_epg(self, channels):
        return {}


class OriginChannels_StandIN():
    def __init__(self):
        pass

    def get_channels(self):
        return []

    def get_channel_stream(self, chandict, allchandict):
        return [{"number": chandict["number"], "stream_url": None}], False


class OriginServiceWrapper():

    def __init__(self, settings, logger, web, db):
        self.config = settings
        self.logger = logger
        self.web = web

        self.servicename = settings.dict["main"]["servicename"]

        self.setup_success = None
        self.setup()

    def setup(self):

        try:
            self.origin = OriginService(self.config, self.logger, self.web)
            self.setup_success = True
            self.logger.info("%s Setup Success" % self.servicename)
        except fHDHR.exceptions.OriginSetupError as e:
            self.logger.error(e)
            self.setup_success = False

        if self.setup_success:
            self.channels = OriginChannels(self.config, self.origin, self.logger, self.web)
            self.epg = OriginEPG(self.config, self.logger, self.web)
        else:
            self.channels = OriginChannels_StandIN()
            self.epg = OriginEPG_StandIN()

    def get_channels(self):
        return self.channels.get_channels()

    def get_channel_stream(self, chandict, allchandict):
        return self.channels.get_channel_stream(chandict, allchandict)

    def update_epg(self, channels):
        return self.epg.update_epg(channels)

    def get_status_dict(self):

        if self.setup_success:
            status_dict = {
                            "Setup": "Success",
                            }

            try:
                full_status_dict = self.origin.get_status_dict()
                for status_key in list(full_status_dict.keys()):
                    status_dict[status_key] = full_status_dict[status_key]
                return status_dict
            except AttributeError:
                return status_dict
        else:
            return {
                    "Setup": "Failed",
                    }

    def __getattr__(self, name):
        ''' will only get called for undefined attributes '''
        if hasattr(self.origin, name):
            return eval("self.origin." + name)
        elif hasattr(self.channels, name):
            return eval("self.channels." + name)
