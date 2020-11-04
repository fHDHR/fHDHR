

from .htmlerror import HTMLerror
from .page_elements import fHDHR_Page_Elements
from .index_html import Index_HTML
from .origin_html import Origin_HTML
from .cluster_html import Cluster_HTML
from .diagnostics_html import Diagnostics_HTML
from .streams_html import Streams_HTML
from .version_html import Version_HTML
from .guide_html import Guide_HTML
from .xmltv_html import xmlTV_HTML


class fHDHR_Pages():

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

        self.page_elements = fHDHR_Page_Elements(fhdhr)

        self.index = Index_HTML(fhdhr, self.page_elements)

        self.htmlerror = HTMLerror(fhdhr)

        self.index = Index_HTML(fhdhr, self.page_elements)
        self.origin = Origin_HTML(fhdhr, self.page_elements)
        self.cluster = Cluster_HTML(fhdhr, self.page_elements)
        self.diagnostics = Diagnostics_HTML(fhdhr, self.page_elements)
        self.version = Version_HTML(fhdhr, self.page_elements)
        self.guide = Guide_HTML(fhdhr, self.page_elements)
        self.streams = Streams_HTML(fhdhr, self.page_elements)
        self.xmltv = xmlTV_HTML(fhdhr, self.page_elements)
