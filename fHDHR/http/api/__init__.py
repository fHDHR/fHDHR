
from .cluster import Cluster
from .channels import Channels
from .lineup_post import Lineup_Post
from .xmltv import xmlTV
from .m3u import M3U
from .epg import EPG
from .debug import Debug_JSON

from .images import Images


class fHDHR_API():

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

        self.cluster = Cluster(fhdhr)
        self.channels = Channels(fhdhr)
        self.xmltv = xmlTV(fhdhr)
        self.m3u = M3U(fhdhr)
        self.epg = EPG(fhdhr)
        self.debug = Debug_JSON(fhdhr)
        self.lineup_post = Lineup_Post(fhdhr)

        self.images = Images(fhdhr)
