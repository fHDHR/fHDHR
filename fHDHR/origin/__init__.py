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

    def get_channel_stream(self, chandict):
        return None


class OriginServiceWrapper():

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

        self.servicename = fhdhr.config.dict["main"]["servicename"]

        self.setup_success = None
        self.setup()

    def setup(self):

        try:
            self.origin = OriginService(self.fhdhr)
            self.setup_success = True
            self.fhdhr.logger.info("%s Setup Success" % self.servicename)
        except fHDHR.exceptions.OriginSetupError as e:
            self.fhdhr.logger.error(e)
            self.setup_success = False

        if self.setup_success:
            self.channels = OriginChannels(self.fhdhr, self.origin)
            self.epg = OriginEPG(self.fhdhr)
        else:
            self.channels = OriginChannels_StandIN()
            self.epg = OriginEPG_StandIN()

    def get_channels(self):
        return self.channels.get_channels()

    def get_channel_stream(self, chandict):
        return self.channels.get_channel_stream(chandict)

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
        if hasattr(self.fhdhr, name):
            return eval("self.fhdhr." + name)
        if hasattr(self.origin, name):
            return eval("self.origin." + name)
        elif hasattr(self.channels, name):
            return eval("self.channels." + name)
        elif hasattr(self.epg, name):
            return eval("self.epg." + name)
        else:
            raise AttributeError(name)
