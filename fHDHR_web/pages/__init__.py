

from .index_html import Index_HTML
from .channels_html import Channels_HTML
from .guide_html import Guide_HTML
from .cluster_html import Cluster_HTML
from .tuners_html import Tuners_HTML
from .xmltv_html import xmlTV_HTML
from .version_html import Version_HTML
from .diagnostics_html import Diagnostics_HTML
from .settings_html import Settings_HTML
from .channels_editor_html import Channels_Editor_HTML
from .tools_html import Tools_HTML


class fHDHR_Pages():

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

        self.index_html = Index_HTML(fhdhr)
        self.channels_html = Channels_HTML(fhdhr)
        self.channels_editor_html = Channels_Editor_HTML(fhdhr)
        self.guide_html = Guide_HTML(fhdhr)
        self.cluster_html = Cluster_HTML(fhdhr)
        self.tuners_html = Tuners_HTML(fhdhr)
        self.xmltv_html = xmlTV_HTML(fhdhr)
        self.version_html = Version_HTML(fhdhr)
        self.diagnostics_html = Diagnostics_HTML(fhdhr)
        self.settings_html = Settings_HTML(fhdhr)
        self.tools_html = Tools_HTML(fhdhr)
