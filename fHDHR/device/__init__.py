from .channels import Channels
from .epg import EPG
from .tuners import Tuners
from .watch import WatchStream
from .images import imageHandler
from .station_scan import Station_Scan
from .ssdp import SSDPServer
from .cluster import fHDHR_Cluster


class fHDHR_Device():

    def __init__(self, settings, fhdhr_version, origin, logger, web, db):

        self.channels = Channels(settings, origin, logger, db)

        self.epg = EPG(settings, self.channels, origin, logger, web, db)

        self.tuners = Tuners(settings, self.epg, logger)

        self.watch = WatchStream(settings, self.channels, self.tuners, logger, web)

        self.images = imageHandler(settings, self.epg, logger, web)

        self.station_scan = Station_Scan(settings, self.channels, logger, db)

        self.ssdp = SSDPServer(settings, fhdhr_version, logger, db)

        self.cluster = fHDHR_Cluster(settings, self.ssdp, logger, db, web)
