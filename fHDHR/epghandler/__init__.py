import time

from fHDHR.epghandler import epgtypes


class EPGhandler():

    def __init__(self, settings, origserv):
        self.config = settings

        self.epg_method = self.config.dict["fhdhr"]["epg_method"]
        if self.epg_method:
            self.sleeptime = self.config.dict[self.epg_method]["epg_update_frequency"]

        self.epgtypes = epgtypes.EPGTypes(settings, origserv)

    def get_thumbnail(self, itemtype, itemid):
        return self.epgtypes.get_thumbnail(itemtype, itemid)


def epgServerProcess(settings, epghandling):
    print("Starting EPG thread...")
    try:

        while True:
            epghandling.epgtypes.update()
            time.sleep(epghandling.sleeptime)

    except KeyboardInterrupt:
        pass
