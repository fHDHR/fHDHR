

from .index_html import Index_HTML
from .origin_html import Origin_HTML
from .cluster_html import Cluster_HTML
from .diagnostics_html import Diagnostics_HTML
from .streams_html import Streams_HTML
from .version_html import Version_HTML
from .guide_html import Guide_HTML
from .xmltv_html import xmlTV_HTML
from .settings import Settings_HTML


class fHDHR_Pages():

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

        self.index = Index_HTML(fhdhr)
        self.settings = Settings_HTML(fhdhr)
        self.origin = Origin_HTML(fhdhr)
        self.cluster = Cluster_HTML(fhdhr)
        self.diagnostics = Diagnostics_HTML(fhdhr)
        self.version = Version_HTML(fhdhr)
        self.guide = Guide_HTML(fhdhr)
        self.streams = Streams_HTML(fhdhr)
        self.xmltv = xmlTV_HTML(fhdhr)
