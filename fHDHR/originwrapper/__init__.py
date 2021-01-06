from .origin_channels_standin import OriginChannels_StandIN
from .origin_epg_standin import OriginEPG_StandIN

import fHDHR.exceptions


class OriginServiceWrapper():

    def __init__(self, fhdhr, origin):
        self.fhdhr = fhdhr
        self.origin = origin

        self.servicename = fhdhr.config.dict["main"]["servicename"]

        self.setup_success = None
        self.setup()

    def setup(self):

        try:
            self.originservice = self.origin.OriginService(self.fhdhr)
            self.setup_success = True
            self.fhdhr.logger.info("%s Setup Success" % self.servicename)
        except fHDHR.exceptions.OriginSetupError as e:
            self.originservice = None
            self.fhdhr.logger.error(e)
            self.setup_success = False

        if self.setup_success:
            self.channels = self.origin.OriginChannels(self.fhdhr, self.originservice)
            self.epg = self.origin.OriginEPG(self.fhdhr)
        else:
            self.channels = OriginChannels_StandIN()
            self.epg = OriginEPG_StandIN()

    def get_channels(self):
        return self.channels.get_channels()

    def get_channel_stream(self, chandict, stream_args):
        return self.channels.get_channel_stream(chandict, stream_args)

    def update_epg(self, channels):
        return self.epg.update_epg(channels)

    def __getattr__(self, name):
        ''' will only get called for undefined attributes '''
        if hasattr(self.fhdhr, name):
            return eval("self.fhdhr." + name)
        if hasattr(self.originservice, name):
            return eval("self.originservice." + name)
        elif hasattr(self.channels, name):
            return eval("self.channels." + name)
        elif hasattr(self.epg, name):
            return eval("self.epg." + name)
        else:
            raise AttributeError(name)
